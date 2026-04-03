import React from 'react';
import { useStore } from '../store/useStore';

export const Controls: React.FC = () => {
    const snapshot = useStore((state) => state.snapshot);
    const config = snapshot?.config;

    const handleAction = async (endpoint: string, body?: any) => {
        try {
            await fetch(`http://localhost:8000${endpoint}`, {
                method: body ? 'POST' : 'GET',
                headers: { 'Content-Type': 'application/json' },
                body: body ? JSON.stringify(body) : undefined,
            });
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div style={{ position: 'absolute', top: 10, left: 10, background: 'rgba(0,0,0,0.8)', color: 'white', padding: 15, borderRadius: 5 }}>
            <h3 style={{ margin: 0, marginBottom: 10 }}>Controls</h3>
            <div>
                <button onClick={() => handleAction('/runner/start', {})}>Start</button>
                <button onClick={() => handleAction('/runner/stop', {})}>Stop</button>
                <button onClick={() => handleAction('/reset', {})}>Reset</button>
                <button onClick={() => handleAction('/tick', {})}>Tick</button>
            </div>
            <div style={{ marginTop: 10 }}>
                <label>Routing: </label>
                <select value={config?.routing_policy || "SHORTEST_PATH"} onChange={(e) => handleAction('/config', { routing_policy: e.target.value })}>
                    <option value="SHORTEST_PATH">SHORTEST_PATH</option>
                    <option value="EPIDEMIC">EPIDEMIC</option>
                    <option value="STORE_AND_FORWARD">STORE_AND_FORWARD</option>
                    <option value="CONTACT_GRAPH_ROUTING">CONTACT_GRAPH_ROUTING</option>
                </select>
            </div>
            <div style={{ marginTop: 10 }}>
                <button onClick={() => handleAction('/chaos', { type: "random_failure", count: 1 })}>Chaos Fail</button>
                <button onClick={() => handleAction('/chaos', { type: "restore_all" })}>Restore</button>
            </div>
        </div>
    );
};