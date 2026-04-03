let socket = null;

const wsUrlInput = document.getElementById("wsUrl");
const connectBtn = document.getElementById("connectBtn");
const tickBtn = document.getElementById("tickBtn");
const resetBtn = document.getElementById("resetBtn");
const runnerStartBtn = document.getElementById("runnerStartBtn");
const runnerStopBtn = document.getElementById("runnerStopBtn");
const streamOffBtn = document.getElementById("streamOffBtn");
const streamOnBtn = document.getElementById("streamOnBtn");
const summary = document.getElementById("summary");
const snapshotPre = document.getElementById("snapshot");

function renderSnapshot(snapshot) {
    const satelliteCount = Object.keys(snapshot.satellites || {}).length;
    const linkCount = (snapshot.links || []).length;
    const packetCount = Object.keys(snapshot.packets || {}).length;
    const metrics = snapshot.metrics || {};
    const runner = snapshot.runner || {};

    summary.innerHTML = `
    <p><strong>Tick:</strong> ${snapshot.tick}</p>
    <p><strong>Satellites:</strong> ${satelliteCount}</p>
    <p><strong>Links:</strong> ${linkCount}</p>
    <p><strong>Packets:</strong> ${packetCount}</p>
    <p><strong>Delivered:</strong> ${metrics.delivered_packets ?? 0}</p>
    <p><strong>Dropped:</strong> ${metrics.dropped_packets ?? 0}</p>
        <p><strong>Runner:</strong> ${runner.running ? "RUNNING" : "STOPPED"}</p>
  `;

    snapshotPre.textContent = JSON.stringify(snapshot, null, 2);
}

function setConnectedState(connected) {
    tickBtn.disabled = !connected;
    resetBtn.disabled = !connected;
    runnerStartBtn.disabled = !connected;
    runnerStopBtn.disabled = !connected;
    streamOffBtn.disabled = !connected;
    streamOnBtn.disabled = !connected;
    connectBtn.textContent = connected ? "Connected" : "Connect";
    connectBtn.disabled = connected;
}

connectBtn.addEventListener("click", () => {
    const url = wsUrlInput.value.trim();
    socket = new WebSocket(url);

    socket.addEventListener("open", () => {
        setConnectedState(true);
    });

    socket.addEventListener("message", (event) => {
        const snapshot = JSON.parse(event.data);
        renderSnapshot(snapshot);
    });

    socket.addEventListener("close", () => {
        setConnectedState(false);
        connectBtn.disabled = false;
        connectBtn.textContent = "Connect";
    });
});

tickBtn.addEventListener("click", () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send("tick");
    }
});

resetBtn.addEventListener("click", () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send("reset");
    }
});

runnerStartBtn.addEventListener("click", () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send("runner:start");
    }
});

runnerStopBtn.addEventListener("click", () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send("runner:stop");
    }
});

streamOffBtn.addEventListener("click", () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send("stream:off");
    }
});

streamOnBtn.addEventListener("click", () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send("stream:on");
    }
});
