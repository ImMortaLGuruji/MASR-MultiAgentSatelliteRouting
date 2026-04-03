import { useStore } from '../store/useStore';
import { bindCameraControls, camera } from './camera';
import {
    drawBackground,
    drawEarth,
    drawLinks,
    drawOrbits,
    drawPackets,
    drawSatellites,
    initStars,
} from './draw';

let canvas: HTMLCanvasElement | null = null;
let ctx: CanvasRenderingContext2D | null = null;
let rotationOffset = 0;

export function initRenderer(canvasElement: HTMLCanvasElement) {
    canvas = canvasElement;
    ctx = canvas.getContext('2d');

    const dpr = window.devicePixelRatio || 1;
    const width = canvas.parentElement!.clientWidth;
    const height = canvas.parentElement!.clientHeight;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx?.scale(dpr, dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    bindCameraControls(canvas);
    initStars(width, height);

    requestAnimationFrame(render);
}

function render() {
    requestAnimationFrame(render);
    if (!ctx || !canvas) {
        return;
    }

    const snapshot = useStore.getState().snapshot;
    const debug = useStore.getState().debug;

    const rect = canvas.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    drawBackground(ctx, width, height);

    if (!snapshot) {
        return;
    }

    rotationOffset += 0.001;

    const center = {
        cx: width / 2 + camera.offsetX,
        cy: height / 2 + camera.offsetY,
    };
    const scale = (Math.min(width, height) / (15000 * 2.2)) * camera.zoom;

    drawEarth(ctx, center, scale);
    drawOrbits(ctx, snapshot, center, scale);
    if (debug.showLinks) {
        drawLinks(ctx, snapshot, center, scale, rotationOffset);
    }
    drawSatellites(ctx, snapshot, center, scale, rotationOffset);
    if (debug.showPackets) {
        drawPackets(ctx, snapshot, center, scale, rotationOffset);
    }
}
