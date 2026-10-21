# EcoCycle AI architecture

EcoCycle AI is a local educational Flask application. The browser loads a responsive HTML template and vanilla JavaScript. The UI calls JSON endpoints under `/api`; the Python application validates inputs, runs the algorithm modules, and reads or writes local JSON files under `data/`.

## Request flow

1. The dashboard requests stored devices and jobs and derives its counts from those records.
2. Device intake validates required fields, ranges, categories, condition, and sample location before appending a UUID-keyed record.
3. Recommendations apply configured age and repair-cost thresholds, then include an explanation and handling note.
4. Route requests build an undirected weighted graph from `locations.json` and run BFS, DFS, Greedy Best-First, or A*. The sample uses a zero heuristic, which is admissible and keeps A* optimal, though it behaves like uniform-cost search.
5. Scheduler requests assign jobs to compatible benches and discrete slots with Min-Conflicts. The result reports conflicts and success explicitly.
6. AI Lab cards send editable JSON examples to `/api/ai/<concept>` and render actual algorithm outputs.

## Storage and safety

`storage.py` resolves paths from its own file location, initializes missing files from defaults, and uses a temporary file plus atomic replacement when saving. Malformed JSON is reported as an error. Device updates preserve unrelated records. This is a single-user classroom demo; JSON files do not provide multi-process locking or production-grade concurrent writes.

Hazardous items are routed to special handling. The app does not instruct users to dismantle batteries, does not offer household disposal, and does not connect to real-world providers, GPS, or collection services. Recommendations are simplified educational rules, not professional assessment.
