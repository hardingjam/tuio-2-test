# me - this DAT.
# webServerDAT - the connected Web Server DAT
# request - A dictionary of the request fields
# response - A dictionary defining the response

import json
import tdu
from pathlib import Path

# Return the response dictionary.
# Serve the index.html/js file and any other files in the webroot.
def onHTTPRequest(webServerDAT, request, response):
	webroot = parent().par.Webroot.eval()
	uri = f"{webroot}{request['uri']}"
	
	if request['uri'] == '/':
		file_path = Path(f"{uri}index.html")
		response['statusCode'] = 200
		response['statusReason'] = 'OK'
		response['data'] = file_path.read_text(encoding='UTF-8')
	
	else:
		file_path = Path(uri)
		if file_path.is_file():
			response['statusCode'] = 200
			response['statusReason'] = 'OK'
			suffix = file_path.suffix
			if suffix in ['.jpg', '.jpeg', '.png', '.svg', '.gif', '.mp4']:
				response['data'] = file_path.read_bytes()
				if suffix in ['.jpg', '.jpeg']:
					response['Content-Type'] = 'image/jpg'
				elif suffix == '.png':
					response['Content-Type'] = 'image/png'
				elif suffix == '.svg':
					response['Content-Type'] = 'image/svg+xml'
				elif suffix == '.gif':
					response['Content-Type'] = 'image/gif'
			elif suffix in ['.woff', '.woff2', '.ttf', '.otf', '.eot']:
				response['data'] = file_path.read_bytes()
				if suffix == '.woff':
					response['Content-Type'] = 'font/woff'
				elif suffix == '.woff2':
					response['Content-Type'] = 'font/woff2'
				elif suffix == '.ttf':
					response['Content-Type'] = 'font/ttf'
				elif suffix == '.otf':
					response['Content-Type'] = 'font/otf'
				elif suffix == '.eot':
					response['Content-Type'] = 'application/vnd.ms-fontobject'
			else:
				response['data'] = file_path.read_text(encoding='UTF-8')
				if suffix == '.js':
					response['Content-Type'] = 'text/javascript'
		else:
			response['statusCode'] = 404
			response['statusReason'] = 'Not Found'

	return response

def onWebSocketOpen(webServerDAT, client):
	debug(f"WebSocket client connected: {client}")
	op('table_clients').appendRow([client, 10])
	return

def onWebSocketClose(webServerDAT, client):
	debug(f"WebSocket client disconnected: {client}")
	tbl = op('table_clients')
	if tbl.row(client):
		tbl.deleteRow(client)
	return

def onWebSocketReceiveText(webServerDAT, client, data):
	
	dataDict = json.loads(data)
	debug(dataDict)
	
	message = dataDict.get('message', None)
	
	debug(f"Websocket received message: {message}")
	
	return


def onWebSocketReceiveBinary(webServerDAT, client, data):
	return

def onServerStart(webServerDAT):
	op('table_clients').clear(keepFirstRow=True)
	return

def onServerStop(webServerDAT):
	op('table_clients').clear(keepFirstRow=True)
	return