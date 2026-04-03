import React from 'react';
import { useStore } from '../store/useStore';

export const Metrics: React.FC = () => {
    const snapshot = useStore((state) => state.snapshot);

    if (!snapshot) return null;

    return (
        <div style={{ position: 'absolute', top: 10, right: 10, background: 'rgba(0,0,0,0.8)', color: 'white', padding: 15, borderRadius: 5, width: 250 }}>
            <h3 style={{ margin: 0, marginBottom: 10 }}>Metrics</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 5 }}>
                <span>Tick:</span> <strong>{snapshot.tick || 0}</strong>
                <span>Satellites:</span> <strong>{snapshot.satellites?.length || 0}</strong>
                <span>Active Links:</span> <strong>{snapshot.links?.length || 0}</strong>
                <span>Packets:</span> <strong>{snapshot.packets?.length || 0}</strong>
                <span>Delivered:</span> <strong>{snapshot.metrics?.delivered_packets || 0}</strong>
                <span>Dropped:</span> <strong>{snapshot.metrics?.dropped_packets || 0}</strong>
            </div>
            {snapshot.config && (
                <div style={{ marginTop: 10, fontSize: '0.8em', color: '#ccc' }}>
                    <div>Policy: {snapshot.config.routing_policy}</div>
                    <div>Drop on Reject: {snapshot.config.drop_on_reject ? 'Yes' : 'No'}</div>
                </div>
            )}
        </div>
    );
};