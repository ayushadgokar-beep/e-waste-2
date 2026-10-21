# Viva questions and concise answers

1. **What problem does EcoCycle AI demonstrate?** Transparent educational e-waste intake and processing decisions.
2. **Why use JSON files?** They are readable, portable, and satisfy the local-file storage requirement for a small demo.
3. **Where are data paths resolved?** Relative to `storage.py`, not the terminal's current directory.
4. **How does the app protect an update from deleting other devices?** It finds and changes one record by ID, then writes the full retained list atomically.
5. **What is BFS?** A graph search that explores nodes in increasing edge-count depth using a queue.
6. **What is DFS?** A graph search that follows a branch deeply using a stack before backtracking.
7. **When is BFS shortest?** In number of edges when all edges have equal cost.
8. **How does Greedy Best-First choose a node?** It chooses the frontier node with the smallest heuristic estimate.
9. **How does A* score a node?** By known path cost `g` plus estimated remaining cost `h`.
10. **Why is the current A* heuristic zero?** It is admissible for the non-negative sample graph; it is simple but reduces A* to uniform-cost search.
11. **What is a state-space search?** A search through states connected by actions to reach a goal state.
12. **What is a CSP?** A set of variables, domains, and constraints whose assignments must be consistent.
13. **How does Min-Conflicts work?** It selects a conflicted variable and changes its value to one that minimizes conflicts.
14. **What makes a bench compatible?** It supports the job's processing type, and hazardous jobs require a designated hazardous resource.
15. **What is a proposition?** A statement that is either true or false under the selected example facts.
16. **What is unification?** Finding substitutions that make two logical terms equal.
17. **Why use an occurs check?** It prevents cyclic substitutions such as `?x = f(?x)`.
18. **How does a reflex agent decide?** It maps only the current observation to an action.
19. **How does a model-based agent differ?** It also stores an internal state, such as prior outcomes.
20. **What does Minimax optimize?** The best outcome assuming an opponent chooses the response least favorable to us.
21. **What does Alpha-Beta pruning do?** It skips branches that cannot change a Minimax decision.
22. **Should Alpha-Beta change the chosen utility?** No, it should match Minimax on the same tree.
23. **Are sample route costs real distances?** No, they are simulated graph weights.
24. **Are recommendations safety certification?** No. They are preliminary classroom rules; hazardous items need appropriate authorized handling.
25. **Does the app contact recyclers or use GPS?** No, it is a self-contained educational simulation.
