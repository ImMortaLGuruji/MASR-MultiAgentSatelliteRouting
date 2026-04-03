import React, { useEffect, useRef } from 'react';
import { Controls } from './components/Controls';
import { Metrics } from './components/Metrics';
import { connectWebSocket } from './websocket/client';
import { initRenderer } from './renderer/canvas';

function App() {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const ws = connectWebSocket('ws://localhost:8000/ws');

        const handleResize = () => {
            if (canvasRef.current) {
                canvasRef.current.width = window.innerWidth;
                canvasRef.current.height = window.innerHeight;
            }
        };

        if (canvasRef.current) {
            initRenderer(canvasRef.current);
            window.addEventListener('resize', handleResize);
            handleResize();
        }

        return () => {
            ws.close();
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    return (
        <div style={{ width: '100vw', height: '100vh', overflow: 'hidden', background: '#0f172a' }}>
            <canvas ref={canvasRef} style={{ display: 'block' }} />
            <Controls />
            <Metrics />
        </div>
    );
}

export default App;