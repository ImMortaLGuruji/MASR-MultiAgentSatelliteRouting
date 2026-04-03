import { camera } from './camera';
import { Snapshot } from '../store/useStore';

const stars: Array<{ x: number; y: number; a: number }> = [];
const visualSatellites = new Map<string, { x: number; y: number; z: number }>();
const packetProgress = new Map<string, number>();

export function initStars(width: number, height: number) {
    if (stars.length > 0) {
        return;
    }
    for (let index = 0; index < 200; index += 1) {
        stars.push({
            x: Math.random() * width,
            y: Math.random() * height,
            a: 0.2 + Math.random() * 0.8,
        });
    }
}

export function project(
    x: number,
    y: number,
    z: number,
    scale: number,
    center: { cx: number; cy: number },
    rotationOffset: number,
) {
    const px = center.cx + (x * Math.cos(rotationOffset) - z * Math.sin(rotationOffset)) * scale;
    const py = center.cy + (y + z * 0.2) * scale;
    return [px, py];
}

export function drawBackground(ctx: CanvasRenderingContext2D, width: number, height: number) {
    ctx.fillStyle = '#020611';
    ctx.fillRect(0, 0, width, height);

    for (const star of stars) {
        ctx.globalAlpha = star.a;
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(star.x, star.y, 1, 1);
    }
    ctx.globalAlpha = 1;
}

export function drawEarth(
    ctx: CanvasRenderingContext2D,
    center: { cx: number; cy: number },
    scale: number,
) {
    const earthRadius = 6371 * scale;

    const gradient = ctx.createRadialGradient(
        center.cx - earthRadius * 0.4,
        center.cy - earthRadius * 0.4,
        earthRadius * 0.1,
        center.cx,
        center.cy,
        earthRadius,
    );
    gradient.addColorStop(0, '#60a5fa');
    gradient.addColorStop(0.55, '#1e3a8a');
    gradient.addColorStop(1, '#020617');

    ctx.shadowBlur = 28;
    ctx.shadowColor = '#3b82f6';
    ctx.beginPath();
    ctx.arc(center.cx, center.cy, earthRadius, 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();
    ctx.lineWidth = 1;
    ctx.strokeStyle = 'rgba(96, 165, 250, 0.45)';
    ctx.stroke();
    ctx.shadowBlur = 0;
}

export function drawOrbits(
    ctx: CanvasRenderingContext2D,
    snapshot: Snapshot,
    center: { cx: number; cy: number },
    scale: number,
) {
    const altitudeSet = new Set<number>();
    snapshot.satellites.forEach((sat) => {
        const dist = Math.sqrt(sat.position.x ** 2 + sat.position.y ** 2 + sat.position.z ** 2);
        altitudeSet.add(Math.round(dist / 50) * 50);
    });

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
    ctx.lineWidth = 1;

    for (const alt of Array.from(altitudeSet).sort((left, right) => left - right)) {
        ctx.beginPath();
        ctx.ellipse(center.cx, center.cy, alt * scale, alt * scale * 0.8, 0, 0, Math.PI * 2);
        ctx.stroke();
    }
}

export function drawLinks(
    ctx: CanvasRenderingContext2D,
    snapshot: Snapshot,
    center: { cx: number; cy: number },
    scale: number,
    rotationOffset: number,
) {
    ctx.globalAlpha = 0.2;
    ctx.lineWidth = 1;
    ctx.strokeStyle = '#60a5fa';

    for (const link of snapshot.links) {
        if (!link.active) {
            continue;
        }
        const sourceVisual = visualSatellites.get(link.source);
        const targetVisual = visualSatellites.get(link.target);
        if (!sourceVisual || !targetVisual) {
            continue;
        }
        const [sx, sy] = project(sourceVisual.x, sourceVisual.y, sourceVisual.z, scale, center, rotationOffset);
        const [tx, ty] = project(targetVisual.x, targetVisual.y, targetVisual.z, scale, center, rotationOffset);
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(tx, ty);
        ctx.stroke();
    }

    ctx.globalAlpha = 1;
}

export function drawSatellites(
    ctx: CanvasRenderingContext2D,
    snapshot: Snapshot,
    center: { cx: number; cy: number },
    scale: number,
    rotationOffset: number,
) {
    for (const sat of snapshot.satellites) {
        const targetX = sat.position.x;
        const targetY = sat.position.y;
        const targetZ = sat.position.z;
        const id = sat.satellite_id;

        if (!visualSatellites.has(id)) {
            visualSatellites.set(id, { x: targetX, y: targetY, z: targetZ });
        } else {
            const current = visualSatellites.get(id)!;
            current.x += (targetX - current.x) * 0.15;
            current.y += (targetY - current.y) * 0.15;
            current.z += (targetZ - current.z) * 0.15;
        }

        const visPosition = visualSatellites.get(id)!;
        const [x, y] = project(visPosition.x, visPosition.y, visPosition.z, scale, center, rotationOffset);

        const bufferUsage = (sat.packet_queue?.length || 0) / Math.max(sat.buffer_capacity || 1, 1);
        const color = bufferUsage > 0.8 ? '#ef4444' : bufferUsage > 0.4 ? '#f59e0b' : '#f8fafc';

        ctx.shadowBlur = 10;
        ctx.shadowColor = color;
        ctx.beginPath();
        ctx.arc(x, y, 4 * camera.zoom, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.shadowBlur = 0;
    }
}

export function drawPackets(
    ctx: CanvasRenderingContext2D,
    snapshot: Snapshot,
    center: { cx: number; cy: number },
    scale: number,
    rotationOffset: number,
) {
    const satById = new Map(snapshot.satellites.map((sat) => [sat.satellite_id, sat]));
    const activePacketIds = new Set(snapshot.packets.map((packet) => packet.packet_id));

    for (const packet of snapshot.packets) {
        const history = packet.route_history || [];
        const fromId = history.length > 1 ? history[history.length - 2] : packet.current_holder;
        const toId = packet.current_holder;
        const fromSat = satById.get(fromId);
        const toSat = satById.get(toId);
        if (!fromSat || !toSat) {
            continue;
        }

        const prevT = packetProgress.get(packet.packet_id) ?? 0;
        const nextT = Math.min(prevT + 0.12, 1);
        packetProgress.set(packet.packet_id, nextT);

        const [fromX, fromY] = project(fromSat.position.x, fromSat.position.y, fromSat.position.z, scale, center, rotationOffset);
        const [toX, toY] = project(toSat.position.x, toSat.position.y, toSat.position.z, scale, center, rotationOffset);

        const x = fromX + (toX - fromX) * nextT;
        const y = fromY + (toY - fromY) * nextT;

        ctx.fillStyle = '#84cc16';
        ctx.fillRect(x, y, 2, 2);
    }

    for (const packetId of Array.from(packetProgress.keys())) {
        if (!activePacketIds.has(packetId)) {
            packetProgress.delete(packetId);
        }
    }
}
