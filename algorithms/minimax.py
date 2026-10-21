TREE={'repair_path':{'bench_busy':-2,'bench_available':4},'recycle_path':{'unsafe_route':-5,'safe_route':3}}


def minimax(tree=TREE):
    moves={}
    for move, outcomes in tree.items(): moves[move]=min(outcomes.values())
    selected=max(moves,key=moves.get)
    return {'move':selected,'utility':moves[selected],'utilities':moves}
