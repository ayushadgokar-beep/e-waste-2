# Practical concepts mapped to EcoCycle AI

| # | Concept | Python module | Website page / endpoint | Example |
|---|---|---|---|---|
| 1 | State-space search | `algorithms/state_space.py` | AI Lab / `state-space` | BFS from unprocessed to special handling |
| 2 | BFS and DFS | `algorithms/graph_search.py` | Routes and AI Lab / `bfs`, `dfs` | North Hub to South Hub |
| 3 | Greedy Best-First and A* | `algorithms/graph_search.py` | Routes and AI Lab / `greedy`, `astar` | Compare path exploration on sample graph |
| 4 | Min-Conflicts CSP | `algorithms/constraint_solver.py` | Scheduler / `min-conflicts` | Assign repair and hazardous jobs to stations |
| 5 | Propositional logic | `algorithms/propositional_logic.py` | AI Lab / `propositional-logic` | Condition and cost facts imply candidate action |
| 6 | Unification | `algorithms/unification.py` | AI Lab / `unification` | `process(?x,battery)` with `process(phone,battery)` |
| 7 | Reflex agent | `algorithms/reflex_agent.py` | AI Lab / `reflex-agent` | Choose based on observed condition |
| 8 | Model-based agent | `algorithms/model_based_agent.py` | AI Lab / `model-based-agent` | Repaired history triggers quality check |
| 9 | Minimax | `algorithms/minimax.py` | AI Lab / `minimax` | Pick strategy with the best worst-case utility |
| 10 | Alpha-Beta pruning | `algorithms/alpha_beta.py` | AI Lab / `alpha-beta` | Same tree and choice with branch counts |

The algorithm modules are independently importable. Route edge costs are simulated values. The default A* heuristic is zero: admissible for non-negative costs, but it offers no geographic guidance. The game-tree utilities are deliberately small invented classroom values.
