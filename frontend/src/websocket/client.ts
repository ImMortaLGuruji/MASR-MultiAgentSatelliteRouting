import {
  useStore,
  Snapshot,
  SatelliteSnapshot,
  PacketSnapshot,
  LinkSnapshot,
  MetricsSnapshot,
} from "../store/useStore";

let pendingSnapshot: Snapshot | null = null;
let frameScheduled = false;
let lastSnapshot: Snapshot | null = null;

type SnapshotDiff = {
  diff: boolean;
  tick?: number;
  changed_satellites?: Record<string, SatelliteSnapshot>;
  changed_packets?: Record<string, PacketSnapshot>;
  removed_packets?: string[];
  links?: LinkSnapshot[] | null;
  metrics?: MetricsSnapshot;
  config?: Record<string, unknown>;
  runner?: Record<string, unknown>;
  satellites?: Record<string, SatelliteSnapshot>;
  packets?: Record<string, PacketSnapshot>;
};

export type WebSocketController = {
  current: WebSocket | null;
  close: () => void;
};

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

export function resetClientState() {
  pendingSnapshot = null;
  frameScheduled = false;
  lastSnapshot = null;
}

export function connectWebSocket(url: string): WebSocketController {
  let active = true;
  const controller: WebSocketController = {
    current: null,
    close: () => {
      active = false;
      controller.current?.close();
      controller.current = null;
    },
  };

  const connect = () => {
    if (!active) {
      return;
    }
    const ws = new WebSocket(url);
    controller.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as SnapshotDiff;
        if (
          data.diff &&
          lastSnapshot &&
          data.tick === 0 &&
          lastSnapshot.tick > 0
        ) {
          lastSnapshot = null;
        }

        let normalizedSnapshot: Snapshot;
        if (data.diff && lastSnapshot) {
          const mergedSatellites = new Map(
            lastSnapshot.satellites.map((sat) => [sat.satellite_id, sat]),
          );
          const mergedPackets = new Map(
            lastSnapshot.packets.map((packet) => [packet.packet_id, packet]),
          );

          for (const [satId, satState] of Object.entries(
            data.changed_satellites || {},
          )) {
            mergedSatellites.set(satId, satState);
          }
          for (const [packetId, packetState] of Object.entries(
            data.changed_packets || {},
          )) {
            mergedPackets.set(packetId, packetState);
          }
          for (const packetId of data.removed_packets || []) {
            mergedPackets.delete(packetId);
          }

          normalizedSnapshot = {
            tick: data.tick ?? lastSnapshot.tick,
            satellites: Array.from(mergedSatellites.values()),
            links: data.links ?? lastSnapshot.links,
            packets: Array.from(mergedPackets.values()),
            metrics: data.metrics ?? lastSnapshot.metrics,
            config: data.config ?? lastSnapshot.config,
            runner: data.runner ?? lastSnapshot.runner,
          };
        } else {
          const satellites = Object.values(data.satellites || {});
          const packets = Object.values(data.packets || {});

          normalizedSnapshot = {
            tick: data.tick ?? 0,
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
      if (!active) {
        return;
      }
      setTimeout(connect, 2000);
    };

    ws.onerror = (e) => {
      console.error("WebSocket error", e);
    };
  };

  connect();

  return controller;
}
