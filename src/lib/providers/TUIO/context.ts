import { getContext, setContext } from 'svelte';
import type { Tuio20Client } from 'tuio-client';

const KEY = 'tuioClient';

export function setTuioClient(client: Tuio20Client) {
	setContext(KEY, client);
}

export function getTuioClient(): Tuio20Client {
	return getContext<Tuio20Client>(KEY);
}
