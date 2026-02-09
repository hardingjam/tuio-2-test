<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import { WebsocketTuioReceiver } from '$lib/modules/WebsocketTuioReceiver';
	import { Tuio20Client } from 'tuio-client';
	import TuioClientProvider from '$lib/providers/TUIO/TUIOClientProvider.svelte';

	let tuioClient = $state<Tuio20Client | null>(null);

	onMount(() => {
		const receiver = new WebsocketTuioReceiver('127.0.0.1', 3333);
		const client = new Tuio20Client(receiver);
		receiver.connect();
		client.connect();
		tuioClient = client;

		return () => {
			client.disconnect();
			receiver.disconnect();
		};
	});

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#if tuioClient}
	<TuioClientProvider client={tuioClient}>
		{@render children?.()}
	</TuioClientProvider>
{/if}
