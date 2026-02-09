import { getTuioClient } from './context';

/**
 * Hook for accessing the Tuio20Client instance from context.
 * Use this hook in child components to access the Tuio20Client instance
 * that was provided by TuioClientProvider.
 *
 * @returns The Tuio20Client instance
 *
 * @example
 * ```svelte
 * <script>
 *   import useTuioClient from '$lib/context/useTuioClient';
 *
 *   const client = useTuioClient();
 *
 *   // Add a TUIO listener
 *   client.addTuioListener(myListener);
 * </script>
 * ```
 */
export default function useTuioClient() {
	return getTuioClient();
}
