import { useStore, Snapshot } from '../store/useStore';

let canvas: HTMLCanvasElement | null = null;
let ctx: CanvasRenderingContext2D | null = null;

// Coordinate projection (isometric/2D simple projection for orbital mechanics)
function project(x: number, y: number, z: number, scale: number = 0.05, center: { cx: number, cy: number }) {
    // Basic pseudo-3D isometric scale or flat projection
    return [
        center.cx + x * scale,
        center.cy + (y + z * 0.5) * scale // Fake depth effect
    ];
}

function getColor(bufferCount: number, capacity: number) {
    if (bufferCount >= capacity * 0.8) return 'red';
    if (bufferCount >= capacity * 0.4) return 'yellow';
    return 'white';
}

function drawEarth(center: { cx: number, cy: number }, scale: number) {
    if (!ctx) return;
    ctx.beginPath();
    ctx.arc(center.cx, center.cy, 6371 * scale, 0, Math.PI * 2);
    ctx.fillStyle = '#1e3a8a'; // Deep blue
    ctx.fill();
    ctx.strokeStyle = '#3b82f6';
    ctx.stroke();
}

function drawSatellites(snapshot: Snapshot, center: { cx: number, cy: number }, scale: number) {
    if (!ctx) return;

    snapshot.satellites.forEach(sat => {
        const [x, y] = project(sat.position.x, sat.position.y, sat.position.z, scale, center);
        const color = getColor(sat.packet_queue?.length || 0, sat.buffer_capacity || 64);

        ctx!.beginPath();
        ctx!.arc(x, y, 4, 0, Math.PI * 2);
        ctx!.fillStyle = color;
        ctx!.fill();
    });
}

function drawLinks(snapshot: Snapshot, center: { cx: number, cy: number }, scale: number) {
    if (!ctx) return;

    // Use a map to quickly lookup satellites by ID since links are source->target IDs
    const satMap = new Map(snapshot.satellites.map(s => [s.satellite_id, s]));

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    snapshot.links.forEach(link => {
        if (!link.active) return;
        const source = satMap.get(link.source);
        const target = satMap.get(link.target);
        if (source && target) {
            const [sx, sy] = project(source.position.x, source.position.y, source.position.z, scale, center);
            const [tx, ty] = project(target.position.x, target.position.y, target.position.z, scale, center);
            ctx!.moveTo(sx, sy);
            ctx!.lineTo(tx, ty);
        }
    });
    ctx.stroke();
}

export function initRenderer(canvasElement: HTMLCanvasElement) {
    canvas = canvasElement;
    ctx = canvas.getContext('2d');

    // Kick off animation loop
    requestAnimationFrame(renderLoop);
}

function renderLoop() {
    requestAnimationFrame(renderLoop);
    if (!ctx || !canvas) return;

    const snapshot = useStore.getState().snapshot;

    // Clear background
    ctx.fillStyle = '#0f172a'; // Deep space background
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (!snapshot) return;

    const center = { cx: canvas.width / 2, cy: canvas.height / 2 };
    const scale = Math.min(canvas.width, canvas.height) / (15000 * 2); // Auto scale max 15000km radius

    drawEarth(center, scale);
    drawLinks(snapshot, center, scale);
    drawSatellites(snapshot, center, scale);
    // Note: To draw packets, we can interpolate position based on holder and tick
    // However, packet mapping and interpolation require historical tracking or progress 
    // fields. For now, draw dots directly at current_holder.
}