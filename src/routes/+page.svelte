<script lang="ts">
	import useTuioClient from '$lib/providers/TUIO/useTuioClient';
	import { Tuio20Canvas } from '$lib/modules/TUIO20Canvas';
	import { onMount } from 'svelte';

	const client = useTuioClient();

	let canvasEl: HTMLCanvasElement;

	onMount(() => {
		const tuioCanvas = new Tuio20Canvas(client, true);
		tuioCanvas.init(canvasEl);
		tuioCanvas.start();

		client.addTuioListener({
			tuioAdd(obj) {
				console.log('ADD', obj);
			},
			tuioUpdate(obj) {
				console.log('UPDATE', obj);
			},
			tuioRemove(obj) {
				console.log('REMOVE', obj);
			},
			tuioRefresh() {}
		});

		return () => tuioCanvas.destroy();
	});
</script>

<canvas bind:this={canvasEl}></canvas>

<style>
	canvas {
		position: fixed;
		inset: 0;
		display: block;
	}
</style>
