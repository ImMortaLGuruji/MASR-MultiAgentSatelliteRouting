import { create } from 'zustand';

export type Snapshot = {
    tick: number;
    satellites: {
        satellite_id: string;
        position: { x: number; y: number; z: number };
        buffer_capacity: number;
        packet_queue: string[];
    }[];
    links: {
        source: string;
        target: string;
        active: boolean;
    }[];
    packets: {
        packet_id: string;
        current_holder: string;
        priority: number;
    }[];
    metrics: {
        throughput?: number;
        delivered_packets?: number;
        dropped_packets?: number;
    };
    config?: any;
    runner?: any;
};

type Store = {
    snapshot: Snapshot | null;
    setSnapshot: (snap: Snapshot) => void;
};

export const useStore = create<Store>((set) => ({
    snapshot: null,
    setSnapshot: (snap) => set({ snapshot: snap }),
}));
