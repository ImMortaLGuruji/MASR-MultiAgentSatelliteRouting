export const camera = {
    zoom: 1,
    offsetX: 0,
    offsetY: 0,
};

let dragging = false;

export function bindCameraControls(canvas: HTMLCanvasElement) {
    canvas.onwheel = (event) => {
        event.preventDefault();
        camera.zoom *= event.deltaY > 0 ? 0.9 : 1.1;
        camera.zoom = Math.max(0.2, Math.min(6, camera.zoom));
    };

    canvas.onmousedown = () => {
        dragging = true;
    };

    window.onmouseup = () => {
        dragging = false;
    };

    canvas.onmousemove = (event) => {
        if (!dragging) {
            return;
        }
        camera.offsetX += event.movementX;
        camera.offsetY += event.movementY;
    };
}
