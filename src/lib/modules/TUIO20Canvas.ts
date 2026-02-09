// Tuio20Canvas.ts
import {
	type Tuio20Bounds,
	type Tuio20Client,
	type Tuio20Listener,
	type Tuio20Object,
	type Tuio20Pointer,
	type Tuio20Symbol,
	type Tuio20Token,
	type TuioTime
} from 'tuio-client';
import { Visuals } from './Visuals';
import { renderSVG } from 'uqr';
import { Vector } from 'vecti';

interface PointerVisual {
	tuioPointer: Tuio20Pointer;
	visual: Visuals;
}

interface TokenVisual {
	tuioToken: Tuio20Token;
	visual: Visuals;
	uuid: string;
	time: number;
}

interface BlobVisual {
	tuioBounds: Tuio20Bounds;
	tuioSymbol: Tuio20Symbol | null;
	visual: Visuals;
}

export class Tuio20Canvas implements Tuio20Listener {
	_canvasWidth: number = 0;
	_canvasHeight: number = 0;
	_sensorWidth: number = 0;
	_sensorHeight: number = 0;
	_flipBounds: boolean;
	_drawingScale: number = 0.8;
	_context: CanvasRenderingContext2D | null = null;
	_size: number[] = [160, 90];
	_colors_2: string[] = [
		'#91d255',
		'#55c8b4',
		'#2896af',
		'#73d2ff',
		'#ffa541',
		'#eb4b50',
		'#f57d7d',
		'#e1afdc',
		'#d2b4a0',
		'#d7af69'
	];
	_colorPointer: number = 0;
	_shouldDraw: boolean = false;
	_drawing: boolean = false;
	_canvas: HTMLCanvasElement | null = null;
	_touches: Map<number, PointerVisual> = new Map();
	_tokens: Map<number, TokenVisual> = new Map();
	_blobs: Map<number, BlobVisual> = new Map();
	_tuio20Client: Tuio20Client;
	_website: string = '';

	private _resizeHandler: (() => void) | null = null;

	constructor(client: Tuio20Client, flipBounds: boolean = false) {
		this._tuio20Client = client;
		this._flipBounds = flipBounds;
		this._tuio20Client.addTuioListener(this);
	}

	public init(canvas: HTMLCanvasElement) {
		this._canvas = canvas;
		this._context = canvas.getContext('2d', { alpha: true });
		this._resizeHandler = this.onWindowResize.bind(this);
		window.addEventListener('resize', this._resizeHandler);
		this.onWindowResize();
	}

	public start() {
		this.clearObjectsAndTouchesList();
		this.startDrawing();
	}

	public stop() {
		this.stopDrawing();
	}

	public destroy() {
		this.stop();
		if (this._resizeHandler) {
			window.removeEventListener('resize', this._resizeHandler);
			this._resizeHandler = null;
		}
		this._canvas = null;
		this._context = null;
	}

	// --- TUIO Listener ---

	public tuioAdd(tuioObject: Tuio20Object) {
		if (tuioObject.containsNewTuioPointer()) {
			this.addTuioPointer(tuioObject.pointer);
		}
		if (tuioObject.containsNewTuioToken()) {
			this.addTuioToken(tuioObject.token);
		}
		if (tuioObject.containsNewTuioBounds()) {
			this.addTuioBounds(tuioObject.bounds, tuioObject.symbol);
		}
	}

	public tuioUpdate(_tuioObject: Tuio20Object) {}

	public tuioRemove(tuioObject: Tuio20Object) {
		if (tuioObject.containsTuioPointer()) {
			this._touches.delete(tuioObject.sessionId);
		}
		if (tuioObject.containsTuioToken()) {
			this._tokens.delete(tuioObject.sessionId);
		}
		if (tuioObject.containsTuioBounds()) {
			this._blobs.delete(tuioObject.sessionId);
		}
	}

	public tuioRefresh(_tuioTime: TuioTime) {
		if (this._tuio20Client?.dim) {
			const width = this._tuio20Client.dim % 65536;
			const height = Math.floor(this._tuio20Client.dim / 65536);
			this._size = this._flipBounds ? [height, width] : [width, height];
		}
	}

	// --- Internal ---

	private getColor() {
		const color = this._colors_2[this._colorPointer];
		this._colorPointer = (this._colorPointer + 1) % this._colors_2.length;
		return color;
	}

	private addTuioPointer(tuioPointer: Tuio20Pointer | null) {
		if (!tuioPointer) return;
		this._touches.set(tuioPointer.sessionId, {
			tuioPointer,
			visual: new Visuals(this.getColor(), true)
		});
	}

	private addTuioBounds(tuioBounds: Tuio20Bounds | null, tuioSymbol: Tuio20Symbol | null) {
		if (!tuioBounds) return;
		this._blobs.set(tuioBounds.sessionId, {
			tuioBounds,
			tuioSymbol,
			visual: new Visuals(this.getColor())
		});
	}

	private addTuioToken(tuioToken: Tuio20Token | null) {
		if (!tuioToken) return;
		this._tokens.set(tuioToken.sessionId, {
			tuioToken,
			visual: new Visuals(this.getColor()),
			uuid: '',
			time: Date.now()
		});
	}

	private clearObjectsAndTouchesList() {
		this._touches = new Map();
		this._tokens = new Map();
		this._blobs = new Map();
	}

	private onWindowResize() {
		this.setCanvasSize(window.innerWidth, window.innerHeight);
	}

	private setCanvasSize(width: number, height: number) {
		if (!this._canvas) return;
		this._canvas.width = width;
		this._canvas.height = height;
		this._canvas.style.width = width + 'px';
		this._canvas.style.height = height + 'px';
		this._canvasWidth = width;
		this._canvasHeight = height;
	}

	private startDrawing() {
		if (!this._shouldDraw) {
			this._shouldDraw = true;
			window.requestAnimationFrame(this.draw.bind(this));
		}
	}

	private stopDrawing() {
		this._shouldDraw = false;
	}

	private draw() {
		if (!this._shouldDraw) {
			this._drawing = false;
			return;
		}
		this._drawing = true;
		this.prepareCanvas();
		this._touches.forEach((t) => this.drawTouch(t));
		this._tokens.forEach((t) => this.drawToken(t));
		this._blobs.forEach((b) => this.drawBlob(b));
		window.requestAnimationFrame(this.draw.bind(this));
		this._drawing = false;
	}

	// --- Drawing ---

	private degToRad(deg: number) {
		return (deg * Math.PI) / 180.0;
	}

	private radToDeg(rad: number) {
		return (rad * 180.0) / Math.PI;
	}

	private strokeRect(
		x: number,
		y: number,
		width: number,
		height: number,
		angle: number,
		radius: number
	) {
		if (!this._context) return;
		if (width < 2 * radius) radius = width / 2;
		if (height < 2 * radius) radius = height / 2;
		this._context.save();
		this._context.translate(x, y);
		this._context.rotate(angle);
		this._context.beginPath();
		this._context.moveTo(-0.5 * width + radius, -0.5 * height);
		this._context.arcTo(0.5 * width, -0.5 * height, 0.5 * width, 0.5 * height, radius);
		this._context.arcTo(0.5 * width, 0.5 * height, -0.5 * width, 0.5 * height, radius);
		this._context.arcTo(-0.5 * width, 0.5 * height, -0.5 * width, -0.5 * height, radius);
		this._context.arcTo(-0.5 * width, -0.5 * height, 0.5 * width, -0.5 * height, radius);
		this._context.stroke();
		this._context.closePath();
		this._context.restore();
	}

	private drawTouch(touch: PointerVisual) {
		if (!this._context) return;
		touch.visual.step();
		const x = (touch.tuioPointer.position.x * this._size[0]) / this._drawingScale;
		const y = (touch.tuioPointer.position.y * this._size[1]) / this._drawingScale;
		const c = touch.visual.getCircle(0);
		this._context.strokeStyle = `rgba(${c.rgbColor?.r},${c.rgbColor?.g},${c.rgbColor?.b},${c.alpha})`;
		this._context.lineWidth = c.thickness;
		this._context.beginPath();
		this._context.arc(x, y, c.radius, this.degToRad(c.rotation), this.degToRad(c.rotation + 315));
		this._context.stroke();
		this._context.closePath();
	}

	private drawToken(token: TokenVisual) {
		if (!this._context) return;
		let x = (token.tuioToken.position.x * this._size[0]) / this._drawingScale;
		let y = (token.tuioToken.position.y * this._size[1]) / this._drawingScale;
		token.visual.step();
		const c = token.visual.getCircle(0);
		this._context.strokeStyle = `rgba(${c.rgbColor?.r},${c.rgbColor?.g},${c.rgbColor?.b},${c.alpha})`;
		this._context.lineWidth = c.thickness;
		this._context.beginPath();
		this._context.arc(x, y, c.radius, this.degToRad(c.rotation), this.degToRad(c.rotation + 315));
		this._context.stroke();
		this._context.closePath();

		const rectWidth = 441;
		const rectHeight = 441;
		x -= rectWidth / 2;
		y -= rectHeight / 2;
		const rotation = token.tuioToken.angle;
		const color = token.visual.getColor();
		this._context.translate(x + rectWidth / 2, y + rectHeight / 2);
		this._context.rotate(rotation);
		this._context.font = 'bold 24px Arial';
		this._context.fillStyle = color;
		this._context.textAlign = 'right';
		this._context.fillText(
			(Math.round(this.radToDeg(rotation)) % 360) + '°',
			-rectWidth / 2 - 20,
			0
		);
		this._context.textAlign = 'left';
		this._context.fillText(
			'ID: ' + (token.tuioToken.cId == 0 ? '-' : token.tuioToken.cId),
			rectWidth / 2 + 20,
			0
		);
		this._context.rotate(-rotation);
		this._context.translate(-(x + rectWidth / 2), -(y + rectHeight / 2));
	}

	private drawBlob(blob: BlobVisual) {
		if (!this._context) return;
		blob.visual.step();
		const c = blob.visual.getCircle(0);
		let x = (blob.tuioBounds.position.x * this._size[0]) / this._drawingScale;
		let y = (blob.tuioBounds.position.y * this._size[1]) / this._drawingScale;
		const r = c.radius - 80;
		const w = (blob.tuioBounds.size.x * this._size[0]) / this._drawingScale + 2 * r;
		const h = (blob.tuioBounds.size.y * this._size[1]) / this._drawingScale + 2 * r;
		this._context.strokeStyle = `rgba(${c.rgbColor?.r},${c.rgbColor?.g},${c.rgbColor?.b},${c.alpha})`;
		this._context.lineWidth = c.thickness;
		this.strokeRect(x, y, w, h, blob.tuioBounds.angle, r);

		x -= w / 2;
		y -= h / 2;
		this._context.translate(x + w / 2, y + h / 2);
		this._context.rotate(blob.tuioBounds.angle);
		this._context.font = 'bold 24px Arial';
		this._context.fillStyle = blob.visual.getColor();
		this._context.textAlign = 'left';
		this._context.fillText('ID: ' + blob.tuioSymbol?.data, w / 2 + 20, 0);
		this._context.rotate(-blob.tuioBounds.angle);
		this._context.translate(-(x + w / 2), -(y + h / 2));
	}

	private drawQrCode(data: string, position: Vector, size: Vector) {
		if (!this._context || !data) return;
		const svg = renderSVG(data);
		const img = new Image();
		img.src = `data:image/svg+xml,${svg}`;
		this._context.drawImage(img, position.x, position.y, size.x, size.y);
	}

	private prepareCanvas() {
		if (!this._context) return;
		this._context.setTransform(1, 0, 0, 1, 0, 0);
		this._context.clearRect(
			-this._canvasWidth,
			-this._canvasHeight,
			this._canvasWidth * 3,
			this._canvasHeight * 3
		);
		this._context.fillStyle = '#1d1d1d';
		this._context.fillRect(
			-this._canvasWidth,
			-this._canvasHeight,
			this._canvasWidth * 3,
			this._canvasHeight * 3
		);

		this._sensorWidth = this._canvasWidth;
		this._sensorHeight = this._canvasHeight;

		if (this._size[0] > 0 && this._size[1] > 0) {
			if (this._sensorWidth / this._sensorHeight > this._size[0] / this._size[1]) {
				this._sensorWidth = (this._sensorHeight * this._size[0]) / this._size[1];
			} else if (this._sensorWidth / this._sensorHeight < this._size[0] / this._size[1]) {
				this._sensorHeight = (this._sensorWidth * this._size[1]) / this._size[0];
			}
		}

		this._context.setTransform(1, 0, 0, 1, 0, 0);
		this._context.translate(
			0.5 * (this._canvasWidth - this._sensorWidth),
			0.5 * (this._canvasHeight - this._sensorHeight)
		);
		this._context.scale(
			(this._drawingScale * this._sensorHeight) / this._size[1],
			(this._drawingScale * this._sensorHeight) / this._size[1]
		);
		this._context.fillStyle = '#000000';
		this._context.fillRect(
			0,
			0,
			this._size[0] / this._drawingScale,
			this._size[1] / this._drawingScale
		);
		this.drawQrCode(this._website, new Vector(0, 0), new Vector(300, 300));
	}
}
