"""First-order unification for variables like ?x and nested tuples (f, arg...)."""
import re


def _var(t): return isinstance(t,str) and t.startswith('?')
def _apply(t, s):
    if _var(t) and t in s: return _apply(s[t],s)
    if isinstance(t,tuple): return tuple(_apply(x,s) for x in t)
    return t
def _occurs(v,t,s):
    t=_apply(t,s)
    return v==t or (isinstance(t,tuple) and any(_occurs(v,x,s) for x in t))
def unify(a,b):
    todo=[(a,b)]; sub={}
    while todo:
        x,y=todo.pop(); x=_apply(x,sub); y=_apply(y,sub)
        if x==y: continue
        if _var(x):
            if _occurs(x,y,sub): return {"success":False,"substitutions":{},"error":f"Occurs check failed: {x} appears inside {y}."}
            sub[x]=y
        elif _var(y): todo.append((y,x))
        elif isinstance(x,tuple) and isinstance(y,tuple) and len(x)==len(y) and x[0]==y[0]: todo.extend(zip(x[1:],y[1:]))
        else: return {"success":False,"substitutions":{},"error":f"Cannot unify {x} with {y}."}
    return {"success":True,"substitutions":{k:_apply(v,sub) for k,v in sub.items()},"error":None}


def parse_term(source):
    source=source.strip()
    if '(' not in source: return source
    name,rest=source.split('(',1)
    if not rest.endswith(')'): raise ValueError('Terms must close with )')
    body=rest[:-1]; args=[]; depth=0; start=0
    for i,ch in enumerate(body):
        if ch=='(': depth+=1
        elif ch==')': depth-=1
        elif ch==',' and depth==0: args.append(body[start:i].strip()); start=i+1
    if body.strip(): args.append(body[start:].strip())
    return (name.strip(),)+tuple(parse_term(x) for x in args)
