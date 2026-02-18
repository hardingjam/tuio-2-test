# me - this DAT
#
# dat - the DAT receiving the TUIO messages
# events - a list of TUIOEvent objects in order of oldest to newest
#
#
# each TUIOEvent objects as the following members
#	timestamp - the TUIO timestamp of this event, in 'seconds since Jan 1, 1900'
#	source - TUIO source string.
#	width - sensor width, up to 65535, TUIO2 only.
#	height - sensor height, up to 65535, TUIO2 only.
# 	touchesStart - a list of touches that started this event
# 	touchesMove - a list of touches that moved this event
#	touchesEnd - a list of touches that ended this event
# 	touchesNoChange - a list of pre-existing touches that didn't move
#						or end this event
#
# each of those touches is a TUIOTouch object which has the following members
#	id
#	profile
#	u, v, w
#	angleX, angleY, angleZ
#	width, height, depth
#	area
#	volume
#	velocityX, velocityY, velocityZ
#	rotationX, rotationY, rotationZ
#	motionAccel
#	rotationAccel
#	classId
# Below are members of touch that are for TUIO2 only:
#	rotationAxisX, rotationAxisY, rotationAxisZ
#	shear
#	radius
#	pressure, pressureVel, pressureAccel
#	typeId, userId
#	symGroup, symData
#	convexHull
#	outerContour, innerContour
#	skeleton, skeletonVolume
#	areaGeometry
#	rawWidth, rawData
#	control
#	datMime, datData
#	sigComponent, sigSessions
#	coaSlot, coaSessions
#	liaType, liaSessions
#	llaType, llaSessions
#	ltaType, ltaSessions
#	(note TUIO2 3d will have rotation axis,
#	 and angle/rotation magnitude will be in angleX, rotationX)

def onTouches(dat, events):
	# Get the webserver DAT
	webserverDAT = parent().parent().op('./web_server/webserver1')

	# Get the streaming mode toggle
	streamConstant = parent().par.Streamconstant.eval()
	debug(streamConstant)

	for event in events:
		# Check if we should skip frames with no changes
		if not streamConstant:
			hasChanges = (len(event.touchesStart) > 0 or
			              len(event.touchesMove) > 0 or
			              len(event.touchesEnd) > 0)
			if not hasChanges:
				continue

		# Determine which touches to send as "set" messages
		if streamConstant:
			changedTouches = event.touchesStart + event.touchesMove + event.touchesNoChange
		else:
			changedTouches = event.touchesStart + event.touchesMove

		# Separate touches by profile type
		pointerTouches = []
		boundsTouches = []
		tokenTouches = []
		symbolTouches = []

		for touch in changedTouches:
			profile = touch.profile
			if "/tuio2/ptr" in profile or profile == "":
				pointerTouches.append(touch)
			elif "/tuio2/bnd" in profile:
				boundsTouches.append(touch)
			elif "/tuio2/tok" in profile:
				tokenTouches.append(touch)
			elif "/tuio2/sym" in profile:
				symbolTouches.append(touch)

		allActiveTouches = event.touchesStart + event.touchesMove + event.touchesNoChange

		# /tuio2/frm — args: [frameId, oscTime, dim, source]
		# dim packs sensor dimensions: (height << 16) | width
		width = int(event.width) if hasattr(event, 'width') else 0
		height = int(event.height) if hasattr(event, 'height') else 0
		dim = (height << 16) | width
		frameId = int(event.timestamp * 1000) & 0xFFFFFFFF
		oscTime = float(event.timestamp)
		source = str(event.source) if hasattr(event, 'source') else "TouchDesigner"
		sendOSC(webserverDAT, "/tuio2/frm", [frameId, oscTime, dim, source])

		# /tuio2/ptr — args: [sessionId, tuId, cId, x, y, angle, shear, radius, press]
		for touch in pointerTouches:
			sendOSC(webserverDAT, "/tuio2/ptr", [
				touch.id,
				touch.userId if hasattr(touch, 'userId') else 0,
				touch.classId,
				touch.u,
				touch.v,
				touch.angleZ,
				touch.shear if hasattr(touch, 'shear') else 0.0,
				touch.radius if hasattr(touch, 'radius') else 0.0,
				touch.pressure if hasattr(touch, 'pressure') else 0.0
			])

		# /tuio2/bnd — args: [sessionId, x, y, angle, sizeW, sizeH, area]
		for touch in boundsTouches:
			sendOSC(webserverDAT, "/tuio2/bnd", [
				touch.id,
				touch.u,
				touch.v,
				touch.angleZ,
				touch.width,
				touch.height,
				touch.area
			])

		# /tuio2/tok — args: [sessionId, tuId, cId, x, y, angle]
		for touch in tokenTouches:
			sendOSC(webserverDAT, "/tuio2/tok", [
				touch.id,
				touch.userId if hasattr(touch, 'userId') else 0,
				touch.classId,
				touch.u,
				touch.v,
				touch.angleZ
			])

		# /tuio2/sym — args: [sessionId, tuId, cId, group, data]
		for touch in symbolTouches:
			group = touch.symGroup if hasattr(touch, 'symGroup') else ""
			data = touch.symData if hasattr(touch, 'symData') else str(touch.classId)
			sendOSC(webserverDAT, "/tuio2/sym", [
				touch.id,
				touch.userId if hasattr(touch, 'userId') else 0,
				touch.classId,
				group,
				data
			])

		# /tuio2/alv — all active session IDs, sent last to trigger frame processing
		allActiveIds = [t.id for t in allActiveTouches]
		sendOSC(webserverDAT, "/tuio2/alv", allActiveIds)

	return

def sendOSC(webserverDAT, address, args):
	"""Send JSON-encoded OSC message to all WebSocket clients.

	Message shape matches what tuio-client's TuioReceiver.onOscMessage() expects:
	  { "address": "/tuio2/xxx", "args": [...] }
	"""
	import json

	msg = {
		"address": address,
		"args": args
	}

	msgJson = json.dumps(msg)
	debug(msgJson)

	for connection in webserverDAT.webSocketConnections:
		webserverDAT.webSocketSendText(msgJson, connection)
