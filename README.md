# EcoCycle AI — E-Waste Collection & Repair Optimizer

EcoCycle AI is a local academic simulation for e-waste intake, transparent repair/reuse/recovery/recycling recommendations, sample route planning, processing-job scheduling, and ten interactive AI practicals. It does not connect to collection companies, GPS, or live services.

## Features

- Dashboard statistics derived from JSON records, category chart, and recent intake.
- Validated device registration, search, and status updates.
- Explainable example recommendations with special handling notes for hazardous items.
- BFS, DFS, Greedy Best-First, and A* on a simulated weighted collection graph.
- Min-Conflicts job assignment to compatible sample benches.
- Interactive demonstrations of state-space search, graph search, CSP, propositional rules, unification, reflex and model-based agents, Minimax, and Alpha-Beta.
- JSON files initialized on first run and saved with atomic replacement.

## Requirements and launch

Python 3.10 or newer is recommended.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>. On systems without `py`, use `python` to create the virtual environment.

## Tests

```powershell
python -m pytest -q
```

## Structure

```text
app.py                  Flask pages and API
storage.py              Validated-path JSON file helpers
recommendations.py      Configurable educational rule engine
algorithms/             Ten standalone AI algorithm modules
data/                   Device, job, location, bench, settings JSON
templates/index.html    Responsive dashboard and interactive pages
static/css/style.css    Visual styling
static/js/app.js        API-connected page behavior and AI Lab
tests/                  API, algorithm, and storage tests
docs/                   Architecture, practical mapping, viva prep
```

## API overview

All API responses use `{ "success": true, "data": ... }` or `{ "success": false, "error": ... }`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/dashboard` | Derived counts and recent devices |
| GET, POST | `/api/devices` | Search/list or register devices |
| GET, PUT | `/api/devices/<id>` | Read or update one device/status |
| GET | `/api/recommendations` | Explain recommendations for all devices |
| POST | `/api/recommendations/<id>` | Compute one recommendation |
| GET | `/api/locations` | Sample route graph |
| POST | `/api/routes` | Compute a route (`bfs`, `dfs`, `greedy`, `astar`) |
| GET, POST | `/api/jobs` | List or add processing jobs |
| POST | `/api/schedule` | Run Min-Conflicts scheduling |
| POST | `/api/ai/<concept>` | Run a practical example |

## JSON storage

Application data lives in `data/` relative to the project files. Missing JSON files are initialized with safe defaults. The provided sample records make the first dashboard useful. Change `settings.json` to adjust the example repair cost ratio and reuse age threshold. This single-user teaching application does not provide database locking for concurrent production use.

## Algorithms and study notes

Read `docs/practical_mapping.md` for the module and UI mapping, `docs/architecture.md` for request and storage flow, and `docs/viva_questions.md` for review questions. A* currently uses an admissible zero heuristic because the sample graph has no geographic coordinates; its path is cost-aware, while the heuristic provides no additional guidance.

## Troubleshooting

- If Flask is missing, activate the virtual environment and rerun `python -m pip install -r requirements.txt`.
- If port 5000 is occupied, stop the other process or run `flask --app app run --port 5001`.
- If a JSON data file is malformed, restore its valid JSON structure; the API returns a controlled error instead of exposing a traceback.
- The displayed route costs are sample units, not road distances. Safety decisions are educational guidance and do not replace authorized handling or professional assessment.
