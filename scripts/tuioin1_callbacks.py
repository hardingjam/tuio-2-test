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
#						or end this event.
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
_frameCounter = 0

def onTouches(dat, events):
	global _frameCounter
	# Get the webserver DAT
	webserverDAT = parent().parent().op('./web_server/webserver1')

	# Get the streaming mode toggle
	streamConstant = parent().par.Streamconstant.eval()
	debug(streamConstant)
	# Loop through the events	
	for event in events:
		# Check if we should skip frames with no changes
		if not streamConstant:
			hasChanges = (len(event.touchesStart) > 0 or
			              len(event.touchesMove) > 0 or
			              len(event.touchesEnd) > 0)
			if not hasChanges:
				continue  # Skip this frame

		# Determine which touches to send as "set" messages
		if streamConstant:
			# Send all active touches every frame
			changedTouches = event.touchesStart + event.touchesMove + event.touchesNoChange
		else:
			# Only send touches that actually changed
			changedTouches = event.touchesStart + event.touchesMove

		# Separate touches by profile type
		pointerTouches = []
		boundsTouches = []
		tokenTouches = []
		symbolTouches = []

		for touch in changedTouches:
			profile = touch.profile or ""
			if "/tuio2/ptr" in profile or profile == "":
				pointerTouches.append(touch)
			elif "/tuio2/bnd" in profile:
				boundsTouches.append(touch)
			elif "/tuio2/tok" in profile:
				tokenTouches.append(touch)
			elif "/tuio2/sym" in profile:
				symbolTouches.append(touch)

		# All active touches for alive messages
		allActiveTouches = event.touchesStart + event.touchesMove + event.touchesNoChange

		# Collect all active session IDs for /tuio2/alv
		allActiveIds = [t.id for t in allActiveTouches]

		# Send POINTER messages (fingers, stylus)
		# /tuio2/ptr set args: [sessionId, tuId, cId, x, y, angle, shear, radius, press]
		for touch in pointerTouches:
			sendOSC(webserverDAT, "/tuio2/ptr", [
				touch.id,       # sessionId
				touch.typeId if hasattr(touch, 'typeId') and touch.typeId is not None else 0,  # tuId
				touch.classId,  # cId
				touch.u or 0.0,
				touch.v or 0.0,
				touch.angleZ or 0.0,
				touch.shear if hasattr(touch, 'shear') and touch.shear is not None else 0.0,
				touch.radius if hasattr(touch, 'radius') and touch.radius is not None else 0.0,
				touch.pressure if hasattr(touch, 'pressure') and touch.pressure is not None else 0.0
			])

		# Send BOUNDS messages (phones, tablets, objects)
		# /tuio2/bnd set args: [sessionId, x, y, angle, size.x, size.y, area]
		for touch in boundsTouches:
			sendOSC(webserverDAT, "/tuio2/bnd", [
				touch.id,       # sessionId
				touch.u or 0.0,
				touch.v or 0.0,
				touch.angleZ or 0.0,
				touch.width or 0.0,
				touch.height or 0.0,
				touch.area or 0.0
			])

		# Send SYMBOL messages
		# /tuio2/sym set args: [sessionId, tuId, cId, group, data]
		for touch in symbolTouches:
			group = touch.symGroup if hasattr(touch, 'symGroup') and touch.symGroup is not None else ""
			data = touch.symData if hasattr(touch, 'symData') and touch.symData is not None else str(touch.classId)
			sendOSC(webserverDAT, "/tuio2/sym", [
				touch.id,       # sessionId
				touch.typeId if hasattr(touch, 'typeId') and touch.typeId is not None else 0,  # tuId
				touch.classId,  # cId
				group,
				data
			])

		# Send TOKEN messages
		# /tuio2/tok set args: [sessionId, tuId, cId, x, y, angle]
		for touch in tokenTouches:
			sendOSC(webserverDAT, "/tuio2/tok", [
				touch.id,       # sessionId
				touch.typeId if hasattr(touch, 'typeId') and touch.typeId is not None else 0,  # tuId
				touch.classId,  # cId
				touch.u or 0.0,
				touch.v or 0.0,
				touch.angleZ or 0.0
			])

		# Send frame message
		# /tuio2/frm args: [frameId, oscTime, dim, source]
		# oscTime is an NTP 64-bit integer sent as a string to preserve precision through JSON
		# event.timestamp is seconds since Jan 1 1900 (NTP epoch)
		_frameCounter += 1
		oscTime = str(int(event.timestamp * (2**32)))
		width = event.width if hasattr(event, 'width') and event.width else 0
		height = event.height if hasattr(event, 'height') and event.height else 0
		dim = (width << 16) | height  # TUIO2 dim encodes width+height as one int
		sendOSC(webserverDAT, "/tuio2/frm", [
			_frameCounter,
			oscTime,
			dim,
			event.source if hasattr(event, 'source') and event.source else "TouchDesigner"
		])

		# Send alive message — must come after frm and component messages
		# /tuio2/alv args: [sessionId, sessionId, ...]
		sendOSC(webserverDAT, "/tuio2/alv", allActiveIds)

	return


def sendOSC(webserverDAT, address, args):
	"""Send OSC message to all WebSocket clients"""
	import json

	msg = {
		"address": address,
		"args": args
	}

	msgJson = json.dumps(msg)
	debug(msgJson)

	# Send to all connected WebSocket clients
	for connection in webserverDAT.webSocketConnections:
		webserverDAT.webSocketSendText(msgJson, connection)
