import { create } from 'zustand';

export type DebugFlags = {
    showLinks: boolean;
    showPackets: boolean;
    showHeatmap: boolean;
};

export type Snapshot = {
    tick: number;
    satellites: {
        satellite_id: string;
        position: { x: number; y: number; z: number };
        buffer_capacity: number;
        packet_queue: string[];
        neighbors?: string[];
    }[];
    links: {
        source: string;
        target: string;
        active: boolean;
    }[];
    packets: {
        packet_id: string;
        current_holder: string;
        route_history?: string[];
        destination?: string;
        priority: number;
    }[];
    metrics: {
        throughput?: number;
        average_latency?: number;
        delivered_packets?: number;
        dropped_packets?: number;
    };
    config?: any;
    runner?: any;
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
