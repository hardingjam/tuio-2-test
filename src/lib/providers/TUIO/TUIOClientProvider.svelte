<script lang="ts">
	import { setTuioClient } from './context';
	import type { Tuio20Client } from 'tuio-client';
	import type { Snippet } from 'svelte';

	let { client, children }: { client: Tuio20Client; children: Snippet } = $props();

	setTuioClient(client);
</script>

{@render children()}
