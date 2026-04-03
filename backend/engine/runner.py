from __future__ import annotations

import threading
import time

from backend.engine.simulation_engine import SimulationEngine


class SimulationRunner:
    def __init__(self, engine: SimulationEngine, tick_interval: float, lock: threading.RLock) -> None:
        self.engine = engine
        self.tick_interval = tick_interval
        self.lock = lock
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> bool:
        if self.is_running:
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="masr-sim-runner", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> bool:
        if not self.is_running:
            return False
        self._stop_event.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=max(self.tick_interval * 2.0, 0.1))
        self._thread = None
        return True

    def _loop(self) -> None:
        next_tick_at = time.monotonic()
        while not self._stop_event.is_set():
            with self.lock:
                self.engine.run_tick()
            next_tick_at += self.tick_interval
            sleep_for = max(0.0, next_tick_at - time.monotonic())
            self._stop_event.wait(sleep_for)
