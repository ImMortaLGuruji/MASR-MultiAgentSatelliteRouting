import { useStore } from "../store/useStore";
import { bindCameraControls, camera } from "./camera";
import {
  drawBackground,
  drawEarth,
  drawHeatmap,
  drawLinks,
  drawOrbits,
  drawPackets,
  drawSatellites,
  initStars,
  resetDrawState,
} from "./draw";

let canvas: HTMLCanvasElement | null = null;
let ctx: CanvasRenderingContext2D | null = null;
let rotationOffset = 0;

function resizeCanvas(width: number, height: number) {
  if (!canvas || !ctx) {
    return;
  }
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(width * dpr));
  canvas.height = Math.max(1, Math.floor(height * dpr));
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.scale(dpr, dpr);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  initStars(width, height, true);
}

export function initRenderer(canvasElement: HTMLCanvasElement) {
  canvas = canvasElement;
  ctx = canvas.getContext("2d");

  resetRendererState();

  bindCameraControls(canvas);

  requestAnimationFrame(render);
}

export function resizeRenderer(container?: HTMLElement) {
  if (!canvas || !ctx) {
    return;
  }
  const parent = container ?? canvas.parentElement;
  if (!parent) {
    return;
  }
  resizeCanvas(parent.clientWidth, parent.clientHeight);
}

export function resetRendererState() {
  rotationOffset = 0;
  resetDrawState();
  if (canvas && ctx) {
    resizeRenderer();
  }
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
  if (debug.showHeatmap) {
    drawHeatmap(ctx, snapshot, center, scale, rotationOffset);
  }
  if (debug.showLinks) {
    drawLinks(ctx, snapshot, center, scale, rotationOffset);
  }
  drawSatellites(ctx, snapshot, center, scale, rotationOffset);
  if (debug.showPackets) {
    drawPackets(ctx, snapshot, center, scale, rotationOffset);
  }
}
