import React, { useEffect, useRef } from "react";
import { Controls } from "./ui/Controls";
import { Metrics } from "./ui/Metrics";
import { connectWebSocket } from "./websocket/client";
import { initRenderer, resizeRenderer } from "./renderer/engine";
import { WS_BASE, API_KEY } from "./config";

function App() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const wsUrl = API_KEY
      ? `${WS_BASE}/ws?api_key=${encodeURIComponent(API_KEY)}`
      : `${WS_BASE}/ws`;
    const wsController = connectWebSocket(wsUrl);

    const handleResize = () => {
      if (containerRef.current) {
        resizeRenderer(containerRef.current);
      }
    };

    if (canvasRef.current) {
      initRenderer(canvasRef.current);
      window.addEventListener("resize", handleResize);
      // small delay to ensure CSS Grid layout has settled before sizing canvas
      setTimeout(handleResize, 10);
    }

    return () => {
      wsController.close();
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <div className="dashboard-layout">
      <div className="panel">
        <Controls />
      </div>

      <div className="canvas-container" ref={containerRef}>
        <canvas ref={canvasRef} style={{ display: "block" }} />
      </div>

      <div className="panel panel-right">
        <Metrics />
      </div>
    </div>
  );
}

export default App;
