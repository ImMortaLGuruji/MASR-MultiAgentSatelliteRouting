let socket = null;

const apiUrlInput = document.getElementById("apiUrl");
const wsUrlInput = document.getElementById("wsUrl");
const connectBtn = document.getElementById("connectBtn");
const tickBtn = document.getElementById("tickBtn");
const resetBtn = document.getElementById("resetBtn");
const runnerStartBtn = document.getElementById("runnerStartBtn");
const runnerStopBtn = document.getElementById("runnerStopBtn");
const streamOffBtn = document.getElementById("streamOffBtn");
const streamOnBtn = document.getElementById("streamOnBtn");
const routingPolicy = document.getElementById("routingPolicy");
const applyRoutingBtn = document.getElementById("applyRoutingBtn");
const tickIntervalInput = document.getElementById("tickInterval");
const dropOnRejectInput = document.getElementById("dropOnReject");
const applyConfigBtn = document.getElementById("applyConfigBtn");
const chaosFailBtn = document.getElementById("chaosFailBtn");
const chaosRestoreBtn = document.getElementById("chaosRestoreBtn");
const chaosPartitionOnBtn = document.getElementById("chaosPartitionOnBtn");
const chaosPartitionOffBtn = document.getElementById("chaosPartitionOffBtn");
const chaosBandwidthBtn = document.getElementById("chaosBandwidthBtn");
const statusLine = document.getElementById("statusLine");
const summary = document.getElementById("summary");
const snapshotPre = document.getElementById("snapshot");

function apiUrl(path) {
    const base = apiUrlInput.value.trim().replace(/\/$/, "");
    return `${base}${path}`;
}

async function postJson(path, body) {
    const response = await fetch(apiUrl(path), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!response.ok) {
        const payload = await response.text();
        throw new Error(`${response.status}: ${payload}`);
    }
    return response.json();
}

async function fetchJson(path) {
    const response = await fetch(apiUrl(path));
    if (!response.ok) {
        const payload = await response.text();
        throw new Error(`${response.status}: ${payload}`);
    }
    return response.json();
}

function setStatus(message) {
    statusLine.textContent = message;
}

function renderSnapshot(snapshot) {
    const satellites = Object.values(snapshot.satellites || {});
    const satelliteCount = satellites.length;
    const linkCount = (snapshot.links || []).length;
    const packetCount = Object.keys(snapshot.packets || {}).length;
    const metrics = snapshot.metrics || {};
    const runner = snapshot.runner || {};
    const config = snapshot.config || {};
    
    let totalBattery = 0;
    let eclipseCount = 0;
    satellites.forEach(s => {
        totalBattery += s.current_battery || 0;
        if(s.in_eclipse) eclipseCount++;
    });
    const avgBattery = satelliteCount > 0 ? (totalBattery / satelliteCount).toFixed(1) : "0.0";

    if (config.routing_policy) {
        routingPolicy.value = config.routing_policy;
    }
    if (typeof config.drop_on_reject === "boolean") {
        dropOnRejectInput.checked = config.drop_on_reject;
    }
    if (typeof config.runner_tick_interval === "number") {
        tickIntervalInput.value = String(config.runner_tick_interval);
    }

    summary.innerHTML = `
    <p><strong>Tick:</strong> ${snapshot.tick}</p>
    <p><strong>Satellites:</strong> ${satelliteCount} (${eclipseCount} in eclipse)</p>
    <p><strong>Avg Battery:</strong> ${avgBattery}/${config.battery_capacity || 100}</p>
    <p><strong>Links:</strong> ${linkCount}</p>
    <p><strong>Packets:</strong> ${packetCount}</p>
    <p><strong>Delivered:</strong> ${metrics.delivered_packets ?? 0}</p>
    <p><strong>Dropped:</strong> ${metrics.dropped_packets ?? 0}</p>
    <p><strong>Runner:</strong> ${runner.running ? "RUNNING" : "STOPPED"}</p>
    <p><strong>Routing:</strong> ${config.routing_policy ?? "-"}</p>
    <p><strong>Drop on Reject:</strong> ${config.drop_on_reject ? "ON" : "OFF"}</p>
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

applyRoutingBtn.addEventListener("click", async () => {
    try {
        const result = await postJson("/set_routing", { policy: routingPolicy.value });
        setStatus(`Routing updated: ${result.policy}`);
    } catch (error) {
        setStatus(`Routing update failed: ${error.message}`);
    }
});

applyConfigBtn.addEventListener("click", async () => {
    try {
        const payload = {
            tick_interval: Number(tickIntervalInput.value),
            drop_on_reject: dropOnRejectInput.checked,
        };
        const result = await postJson("/config", payload);
        setStatus(`Config updated. tick_interval=${result.runner_tick_interval}`);
    } catch (error) {
        setStatus(`Config update failed: ${error.message}`);
    }
});

chaosFailBtn.addEventListener("click", async () => {
    try {
        const result = await postJson("/chaos", {
            mode: "random_satellite_failure",
            count: 1,
        });
        setStatus(`Disabled satellites: ${(result.disabled || []).join(", ") || "none"}`);
    } catch (error) {
        setStatus(`Chaos failed: ${error.message}`);
    }
});

chaosRestoreBtn.addEventListener("click", async () => {
    try {
        const result = await postJson("/chaos", { mode: "restore_satellites", count: 1 });
        setStatus(`Restored satellites: ${(result.restored || []).join(", ") || "none"}`);
    } catch (error) {
        setStatus(`Restore failed: ${error.message}`);
    }
});

chaosPartitionOnBtn.addEventListener("click", async () => {
    try {
        await postJson("/chaos", { mode: "network_partition", enabled: true, count: 1 });
        setStatus("Network partition enabled.");
    } catch (error) {
        setStatus(`Partition enable failed: ${error.message}`);
    }
});

chaosPartitionOffBtn.addEventListener("click", async () => {
    try {
        await postJson("/chaos", { mode: "network_partition", enabled: false, count: 1 });
        setStatus("Network partition disabled.");
    } catch (error) {
        setStatus(`Partition disable failed: ${error.message}`);
    }
});

chaosBandwidthBtn.addEventListener("click", async () => {
    try {
        await postJson("/chaos", { mode: "bandwidth_fluctuation", count: 1 });
        setStatus("Bandwidth fluctuation applied.");
    } catch (error) {
        setStatus(`Bandwidth fluctuation failed: ${error.message}`);
    }
});

fetchJson("/config")
    .then((config) => {
        routingPolicy.value = config.routing_policy;
        dropOnRejectInput.checked = Boolean(config.drop_on_reject);
        tickIntervalInput.value = String(config.runner_tick_interval ?? 1.0);
    })
    .catch(() => {
        setStatus("Could not load config from API.");
    });
