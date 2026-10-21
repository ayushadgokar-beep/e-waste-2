"""Graph traversal and heuristic route-search demonstrations."""
from collections import deque
import heapq


def _path(parent, goal):
    if goal is None or goal not in parent:
        return []
    path=[]
    while goal is not None:
        path.append(goal); goal=parent[goal]
    return list(reversed(path))


def _cost(graph, path):
    return sum(graph[a][b] for a,b in zip(path,path[1:]))


def _result(graph, parent, goal, order, edges):
    path=_path(parent,goal)
    seen=set(); explored=[]
    for a,b in edges:
        key=frozenset((a,b))
        if key not in seen:
            seen.add(key); explored.append([a,b])
    return {"visited":order,"path":path,"cost":_cost(graph,path) if path else None,
            "explored_edges":explored,
            "steps":[{"step":i+1,"node":node,"event":"expanded"} for i,node in enumerate(order)]}


def bfs(graph, start, goal=None):
    visited,parent,order={start},{start:None},[]
    queue=deque([start]); edges=[]
    while queue:
        node=queue.popleft(); order.append(node)
        if node==goal: break
        for neighbor in graph.get(node,{}):
            edges.append((node,neighbor))
            if neighbor not in visited:
                visited.add(neighbor); parent[neighbor]=node; queue.append(neighbor)
    return _result(graph,parent,goal,order,edges)


def dfs(graph, start, goal=None):
    parent,order,stack={start:None},[],[start]
    visited=set(); edges=[]
    while stack:
        node=stack.pop()
        if node in visited: continue
        visited.add(node); order.append(node)
        if node==goal: break
        neighbors=list(graph.get(node,{}))
        for neighbor in reversed(neighbors):
            edges.append((node,neighbor))
            if neighbor not in visited:
                parent.setdefault(neighbor,node); stack.append(neighbor)
    return _result(graph,parent,goal,order,edges)


def greedy_best_first(graph, start, goal, heuristic):
    frontier,parent,seen,order=[(heuristic.get(start,0),start)],{start:None},set(),[]
    edges=[]
    while frontier:
        _,node=heapq.heappop(frontier)
        if node in seen: continue
        seen.add(node); order.append(node)
        if node==goal: break
        for neighbor in graph.get(node,{}):
            edges.append((node,neighbor))
            if neighbor not in seen:
                parent.setdefault(neighbor,node); heapq.heappush(frontier,(heuristic.get(neighbor,0),neighbor))
    return _result(graph,parent,goal,order,edges)


def astar(graph, start, goal, heuristic):
    frontier,parent,g,closed,order=[(heuristic.get(start,0),0,start)],{start:None},{start:0},set(),[]
    edges=[]
    while frontier:
        _,cost,node=heapq.heappop(frontier)
        if node in closed: continue
        closed.add(node); order.append(node)
        if node==goal: break
        for neighbor,edge in graph.get(node,{}).items():
            edges.append((node,neighbor))
            new_cost=cost+edge
            if new_cost<g.get(neighbor,float('inf')):
                g[neighbor]=new_cost; parent[neighbor]=node
                heapq.heappush(frontier,(new_cost+heuristic.get(neighbor,0),new_cost,neighbor))
    return _result(graph,parent,goal,order,edges)
