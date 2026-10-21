from .minimax import TREE


def alpha_beta(tree=TREE):
    alpha=float('-inf'); beta=float('inf'); best=None; best_value=float('-inf'); evaluated=0; pruned=0
    for move,outcomes in tree.items():
        value=float('inf')
        vals=list(outcomes.values())
        for i,utility in enumerate(vals):
            evaluated+=1; value=min(value,utility)
            if value<=alpha:
                pruned+=len(vals)-i-1; break
        if value>best_value: best,best_value=move,value
        alpha=max(alpha,best_value)
    return {'move':best,'utility':best_value,'evaluated':evaluated,'pruned':pruned}
