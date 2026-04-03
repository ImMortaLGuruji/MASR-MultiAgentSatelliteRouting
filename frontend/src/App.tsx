import React, { useEffect, useRef } from 'react';
import { Controls } from './ui/Controls';
import { Metrics } from './ui/Metrics';
import { connectWebSocket } from './websocket/client';
import { initRenderer } from './renderer/engine';

function App() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const ws = connectWebSocket('ws://localhost:8000/ws');

        const handleResize = () => {
            if (canvasRef.current && containerRef.current) {
                canvasRef.current.width = containerRef.current.clientWidth;
                canvasRef.current.height = containerRef.current.clientHeight;
            }
        };

        if (canvasRef.current) {
            initRenderer(canvasRef.current);
            window.addEventListener('resize', handleResize);
            // small delay to ensure CSS Grid layout has settled before sizing canvas
            setTimeout(handleResize, 10);
        }

        return () => {
            ws.close();
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    return (
        <div className="dashboard-layout">
            <div className="panel">
                <Controls />
            </div>

            <div className="canvas-container" ref={containerRef}>
                <canvas ref={canvasRef} style={{ display: 'block' }} />
            </div>

            <div className="panel panel-right">
                <Metrics />
            </div>
        </div>
    );
}

export default App;
