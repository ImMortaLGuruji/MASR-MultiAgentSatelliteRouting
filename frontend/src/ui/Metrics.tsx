import React from 'react';
import { useStore } from '../store/useStore';

export const Metrics: React.FC = () => {
    const snapshot = useStore((state) => state.snapshot);

    if (!snapshot) {
        return null;
    }

    const throughput = snapshot.metrics?.throughput || 0;
    const latency = snapshot.metrics?.average_latency || 0;

    return (
        <>
            <h2 className="panel-title">Telemetry</h2>

            <section className="panel-section">
                <div className="section-title">System</div>
                <div className="metric-row"><span>Tick</span><strong>{snapshot.tick}</strong></div>
                <div className="metric-row"><span>Satellites</span><strong>{snapshot.satellites?.length || 0}</strong></div>
            </section>

            <section className="panel-section">
                <div className="section-title">Network</div>
                <div className="metric-row"><span>Packets</span><strong>{snapshot.packets?.length || 0}</strong></div>
                <div className="metric-row"><span>Delivered</span><strong>{snapshot.metrics?.delivered_packets || 0}</strong></div>
                <div className="metric-row"><span>Dropped</span><strong>{snapshot.metrics?.dropped_packets || 0}</strong></div>
                <div className="metric-row"><span>Links</span><strong>{snapshot.links?.length || 0}</strong></div>
            </section>

            <section className="panel-section">
                <div className="section-title">Performance</div>
                <div className="metric-row"><span>Latency</span><strong>{latency.toFixed(1)} ms</strong></div>
                <div className="metric-row"><span>Throughput</span><strong>{throughput.toFixed(1)} pkt/s</strong></div>
            </section>
        </>
    );
};
