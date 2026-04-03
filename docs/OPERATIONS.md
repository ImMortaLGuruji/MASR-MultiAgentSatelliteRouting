# MASR Operations

## Reproducible Local Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start backend API:

```bash
python -m backend.main
```

3. Start frontend static server:

```bash
cd frontend
python -m http.server 5500
```

4. Open http://localhost:5500 and connect to ws://localhost:8000/ws.

## Routine Commands

- Run tests: `python -m unittest discover -s tests -v`
- Start background runner: `POST /runner/start`
- Stop background runner: `POST /runner/stop`
- Update runtime config: `POST /config`

## Determinism Checklist

- Use seeded config values.
- Keep sorted iteration in agent/message processing.
- Use API `/reset` before reproducibility comparisons.
- Avoid manual mutation outside API/engine methods.
