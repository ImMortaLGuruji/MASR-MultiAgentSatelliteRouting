import { create } from "zustand";

export type DebugFlags = {
  showLinks: boolean;
  showPackets: boolean;
  showHeatmap: boolean;
};

export type SatelliteSnapshot = {
  satellite_id: string;
  position: { x: number; y: number; z: number };
  buffer_capacity: number;
  packet_queue: string[];
  neighbors?: string[];
  routing_policy?: string;
  current_battery?: number;
  in_eclipse?: boolean;
};

export type LinkSnapshot = {
  source: string;
  target: string;
  active: boolean;
  bandwidth?: number;
  delay?: number;
  quality?: number;
};

export type PacketSnapshot = {
  packet_id: string;
  current_holder: string;
  route_history?: string[];
  destination?: string;
  priority: number;
  state?: string;
};

export type MetricsSnapshot = {
  throughput?: number;
  average_latency?: number;
  delivered_packets?: number;
  dropped_packets?: number;
  link_utilization?: number;
  buffer_usage?: number;
};

export type ConfigSnapshot = {
  routing_policy?: string;
  [key: string]: unknown;
};

export type Snapshot = {
  tick: number;
  satellites: SatelliteSnapshot[];
  links: LinkSnapshot[];
  packets: PacketSnapshot[];
  metrics: MetricsSnapshot;
  config?: ConfigSnapshot;
  runner?: Record<string, unknown>;
  failed_satellites?: string[];
  network_partition_enabled?: boolean;
};

type Store = {
  snapshot: Snapshot | null;
  debug: DebugFlags;
  setSnapshot: (snap: Snapshot) => void;
  setDebugFlag: (key: keyof DebugFlags, value: boolean) => void;
};

export const useStore = create<Store>((set) => ({
  snapshot: null,
  debug: {
    showLinks: true,
    showPackets: true,
    showHeatmap: false,
  },
  setSnapshot: (snap) => set({ snapshot: snap }),
  setDebugFlag: (key, value) =>
    set((state) => ({
      debug: {
        ...state.debug,
        [key]: value,
      },
    })),
}));
