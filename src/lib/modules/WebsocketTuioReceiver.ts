import { TuioReceiver } from 'tuio-client';

export class WebsocketTuioReceiver extends TuioReceiver {
	private readonly _url: string;
	private _ws: WebSocket | null = null;

	constructor(host: string, port: number) {
		super();
		this._url = `ws://${host}:${port}`;
	}

	public connect() {
		this._ws = new WebSocket(this._url);
		this._ws.onmessage = (event) => {
			try {
				const msg = JSON.parse(event.data);
				this.onOscMessage(msg);
			} catch {
				// ignore malformed messages
			}
		};
		this.isConnected = true;
	}

	public disconnect() {
		this._ws?.close();
		this._ws = null;
		this.isConnected = false;
	}
}
