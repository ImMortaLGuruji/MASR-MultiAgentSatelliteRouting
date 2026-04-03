import { useStore, Snapshot } from '../store/useStore';

export function connectWebSocket(url: string) {
    const ws = new WebSocket(url);

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            // Format incoming backend snapshot into the structure expected by the Store
            // MASR backend usually sends dictionaries, let's normalize them into arrays for D3/Canvas.
            const satellites = Object.values(data.satellites || {}) as any[];
            const packets = Object.values(data.packets || {}) as any[];

            const normalizedSnapshot: Snapshot = {
                tick: data.tick || 0,
                satellites,
                links: data.links || [],
                packets,
                metrics: data.metrics || {},
                config: data.config || {},
                runner: data.runner || {},
            };

            useStore.getState().setSnapshot(normalizedSnapshot);
        } catch (e) {
            console.error("Malformed snapshot ignored", e);
        }
    };

    ws.onclose = () => {
        setTimeout(() => connectWebSocket(url), 2000); // Retry logic
    };

    ws.onerror = (e) => {
        console.error("WebSocket error", e);
    };

    return ws;
}