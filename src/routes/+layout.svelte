<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import { WebsocketTuioReceiver } from '$lib/modules/WebsocketTuioReceiver';
	import { Tuio20Client } from 'tuio-client';
	import TuioClientProvider from '$lib/providers/TUIO/TUIOClientProvider.svelte';
	import TUIODebugger from '$lib/components/TUIODebugger.svelte';
	import SmartphonesProvider from '$lib/providers/Smartphones/SmartphonesProvider.svelte';
	import { SmartphoneRegistry } from '$lib/providers/Smartphones/SmartphoneRegistry.svelte';
	import { TableSocket } from '$lib/socket/TableSocket.svelte';

	let tuioClient = $state<Tuio20Client | null>(null);

	const registry = new SmartphoneRegistry();
	
	const tableSocket = new TableSocket({
		url: 'wss://tuio-ws-production.up.railway.app?room=test&role=table'
	});

	// Route incoming messages to the registry
	tableSocket.onJoin = (msg) => {
		registry.addPhone(msg.senderId);
	};

	tableSocket.onContactInfo = (msg) => {
		registry.updateContactInfo(msg.senderId, {
			firstName: msg.firstName,
			lastName: msg.lastName,
			email: msg.email,
			company: msg.company
		});
	};

	tableSocket.onPlaced = (msg) => {
		registry.addPlacedSignal(msg.senderId);
	};

	onMount(() => {
		const receiver = new WebsocketTuioReceiver('10.10.110.21', 3333);
		const client = new Tuio20Client(receiver);
		receiver.connect();
		client.connect();
		tuioClient = client;

		tableSocket.connect();

		// Listen for TUIO bounds+symbol → attempt pairing → send tuio-pair
		client.addTuioListener({
			tuioAdd(obj) {
				if (obj.containsNewTuioBounds() && obj.symbol) {
					const deviceId = obj.symbol.data;
					if (!deviceId) return;

					const pairedSenderId = registry.tryPair(deviceId);
					if (pairedSenderId) {
						tableSocket.sendTuioPair(pairedSenderId, deviceId);
					}
				}
			},
			tuioUpdate() {},
			tuioRemove() {},
			tuioRefresh() {}
		});

		return () => {
			client.disconnect();
			receiver.disconnect();
			tableSocket.disconnect();
		};
	});

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#if tuioClient}
	<TuioClientProvider client={tuioClient}>
		<SmartphonesProvider {registry}>
			<TUIODebugger />
			{@render children?.()}
		</SmartphonesProvider>
	</TuioClientProvider>
{/if}
