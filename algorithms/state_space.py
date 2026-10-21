from collections import deque

STATES = {"unprocessed": ["inspected"], "inspected": ["repair", "reuse", "recover", "recycle", "special_handling"], "repair": [], "reuse": [], "recover": [], "recycle": [], "special_handling": []}


def processing_plan(start="unprocessed", goal="recycle"):
    queue=deque([(start,[start])]); visited={start}
    while queue:
        state,path=queue.popleft()
        if state==goal: return {"path":path,"actions":path[1:],"visited":list(visited)}
        for nxt in STATES.get(state,[]):
            if nxt not in visited: visited.add(nxt); queue.append((nxt,path+[nxt]))
    return {"path":[],"actions":[],"visited":list(visited)}
