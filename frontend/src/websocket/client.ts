import { useStore, Snapshot } from '../store/useStore';

let pendingSnapshot: Snapshot | null = null;
let frameScheduled = false;
let lastSnapshot: Snapshot | null = null;

function scheduleSnapshotCommit(snapshot: Snapshot) {
    pendingSnapshot = snapshot;
    if (frameScheduled) {
        return;
    }
    frameScheduled = true;
    requestAnimationFrame(() => {
        frameScheduled = false;
        if (pendingSnapshot) {
            useStore.getState().setSnapshot(pendingSnapshot);
            pendingSnapshot = null;
        }
    });
}

export function connectWebSocket(url: string) {
    const ws = new WebSocket(url);

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            let normalizedSnapshot: Snapshot;
            if (data.diff && lastSnapshot) {
                const mergedSatellites = new Map(
                    lastSnapshot.satellites.map((sat) => [sat.satellite_id, sat])
                );
                const mergedPackets = new Map(
                    lastSnapshot.packets.map((packet: any) => [packet.packet_id, packet])
                );

                for (const [satId, satState] of Object.entries(data.changed_satellites || {})) {
                    mergedSatellites.set(satId, satState as any);
                }
                for (const [packetId, packetState] of Object.entries(data.changed_packets || {})) {
                    mergedPackets.set(packetId, packetState as any);
                }
                for (const delta of data.packets_delta || []) {
                    if (delta?.deleted && delta.packet_id) {
                        mergedPackets.delete(delta.packet_id);
                        continue;
                    }
                    if (delta?.packet_id) {
                        const existing = mergedPackets.get(delta.packet_id) || {};
                        mergedPackets.set(delta.packet_id, { ...existing, ...delta });
                    }
                }
                for (const packetId of data.removed_packets || []) {
                    mergedPackets.delete(packetId);
                }

                normalizedSnapshot = {
                    tick: data.tick || lastSnapshot.tick,
                    satellites: Array.from(mergedSatellites.values()) as any[],
                    links: data.links || lastSnapshot.links,
                    packets: Array.from(mergedPackets.values()) as any[],
                    metrics: data.metrics || lastSnapshot.metrics,
                    config: data.config || lastSnapshot.config,
                    runner: data.runner || lastSnapshot.runner,
                };
            } else {
                const satellites = Object.values(data.satellites || {}) as any[];
                const packets = Object.values(data.packets || {}) as any[];

                normalizedSnapshot = {
                    tick: data.tick || 0,
                    satellites,
                    links: data.links || [],
                    packets,
                    metrics: data.metrics || {},
                    config: data.config || {},
                    runner: data.runner || {},
                };
            }

            lastSnapshot = normalizedSnapshot;

            scheduleSnapshotCommit(normalizedSnapshot);
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