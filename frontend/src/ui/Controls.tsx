import React, { useState } from 'react';
import { useStore } from '../store/useStore';

export const Controls: React.FC = () => {
    const [packetCount, setPacketCount] = useState<number>(15);
    const snapshot = useStore((state) => state.snapshot);
    const debug = useStore((state) => state.debug);
    const setDebugFlag = useStore((state) => state.setDebugFlag);
    const config = snapshot?.config;

    const handleAction = async (endpoint: string, body?: any) => {
        try {
            await fetch(`http://localhost:8000${endpoint}`, {
                method: body ? 'POST' : 'GET',
                headers: { 'Content-Type': 'application/json' },
                body: body ? JSON.stringify(body) : undefined,
            });
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <>
            <h2 className="panel-title">Mission Control</h2>

            <section className="panel-section">
                <div className="section-title">Simulation</div>
                <div className="button-grid">
                    <button className="btn btn-success" onClick={() => handleAction('/runner/start', {})}>Start</button>
                    <button className="btn btn-danger" onClick={() => handleAction('/runner/stop', {})}>Pause</button>
                    <button className="btn" onClick={() => handleAction('/tick', {})}>Step</button>
                    <button className="btn" onClick={() => handleAction('/reset', {})}>Reset</button>
                </div>
            </section>

            <section className="panel-section">
                <div className="section-title">Routing</div>
                <select
                    className="select-box"
                    value={config?.routing_policy || 'SHORTEST_PATH'}
                    onChange={(event) => handleAction('/config', { routing_policy: event.target.value })}
                >
                    <option value="SHORTEST_PATH">Shortest Path</option>
                    <option value="EPIDEMIC">Epidemic</option>
                    <option value="STORE_AND_FORWARD">Store & Forward</option>
                    <option value="CONTACT_GRAPH_ROUTING">CGR</option>
                </select>
            </section>

            <section className="panel-section">
                <div className="section-title">Chaos</div>
                <div className="button-stack">
                    <input
                        className="select-box"
                        type="number"
                        min={1}
                        step={1}
                        value={packetCount}
                        onChange={(event) => {
                            const parsed = Number.parseInt(event.target.value, 10);
                            if (Number.isNaN(parsed)) {
                                setPacketCount(1);
                                return;
                            }
                            setPacketCount(Math.max(1, parsed));
                        }}
                    />
                    <button
                        className="btn"
                        onClick={() =>
                            handleAction('/chaos', {
                                mode: 'mass_packet_generation',
                                count: packetCount,
                            })
                        }
                    >
                        Trigger Traffic
                    </button>
                    <button className="btn btn-danger" onClick={() => handleAction('/chaos', { mode: 'random_satellite_failure', count: 1 })}>
                        Trigger Chaos
                    </button>
                    <button className="btn btn-success" onClick={() => handleAction('/chaos', { mode: 'restore_satellites' })}>
                        Restore
                    </button>
                </div>
            </section>

            <section className="panel-section">
                <div className="section-title">Debug</div>
                <label className="toggle-row">
                    <input
                        type="checkbox"
                        checked={debug.showLinks}
                        onChange={(event) => setDebugFlag('showLinks', event.target.checked)}
                    />
                    Show Links
                </label>
                <label className="toggle-row">
                    <input
                        type="checkbox"
                        checked={debug.showPackets}
                        onChange={(event) => setDebugFlag('showPackets', event.target.checked)}
                    />
                    Show Packets
                </label>
                <label className="toggle-row">
                    <input
                        type="checkbox"
                        checked={debug.showHeatmap}
                        onChange={(event) => setDebugFlag('showHeatmap', event.target.checked)}
                    />
                    Show Heatmap
                </label>
            </section>
        </>
    );
};
