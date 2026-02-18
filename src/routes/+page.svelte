<script lang="ts">
	import useTuioClient from '$lib/providers/TUIO/useTuioClient';
	import { Tuio20Canvas } from '$lib/modules/TUIO20Canvas';
	import { onMount } from 'svelte';

	const client = useTuioClient();

	let canvasEl: HTMLCanvasElement;
	let wsConnected = $state(false);
	let wsError = $state('');

	const clientId = crypto.randomUUID();

	onMount(() => {
		const tuioCanvas = new Tuio20Canvas(client, true);
		tuioCanvas.init(canvasEl);
		tuioCanvas.start();

		// WebSocket relay connection
		const socket = new WebSocket('wss://tuio-ws-production.up.railway.app?room=test');

		socket.addEventListener('open', () => {
			wsConnected = true;
			wsError = '';
			console.log('[WS Relay] Connected');
		});

		socket.addEventListener('close', () => {
			wsConnected = false;
			console.log('[WS Relay] Disconnected');
		});

		socket.addEventListener('error', (e) => {
			wsError = 'WebSocket connection error';
			console.error('[WS Relay] Error', e);
		});

		socket.addEventListener('message', (event) => {
			console.log('[WS Relay] Received:', event.data);
		});

		function sendToRelay(text: string) {
			if (socket.readyState !== WebSocket.OPEN) return;
			try {
				socket.send(JSON.stringify({
					text,
					sender: 'TUIO',
					senderId: clientId
				}));
			} catch (err) {
				console.error('[WS Relay] Failed to send:', err);
			}
		}

		client.addTuioListener({
			tuioAdd(obj) {
				sendToRelay('[TUIO ADD]');
			},
			tuioUpdate(obj) {
				// sendToRelay('[TUIO UPDATE]');
			},
			tuioRemove(obj) {
				sendToRelay('[TUIO REMOVE]');
			},
			tuioRefresh() {}
		});

		return () => {
			tuioCanvas.destroy();
			socket.close();
		};
	});
</script>

<div class="status" class:connected={wsConnected}>
	{wsConnected ? '● Relay connected' : '○ Relay disconnected'}
	{#if wsError}<span class="error">{wsError}</span>{/if}
</div>

<canvas bind:this={canvasEl}></canvas>

<style>
	canvas {
		position: fixed;
		inset: 0;
		display: block;
	}

	.status {
		position: fixed;
		top: 8px;
		right: 8px;
		z-index: 10;
		padding: 4px 10px;
		border-radius: 4px;
		font-size: 12px;
		font-family: monospace;
		background: rgba(0, 0, 0, 0.7);
		color: #f66;
	}

	.status.connected {
		color: #6f6;
	}

	.error {
		color: #f66;
		margin-left: 8px;
	}
</style>