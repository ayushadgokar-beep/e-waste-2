def evaluate(facts):
    hazardous=bool(facts.get('hazardous') or facts.get('condition')=='hazardous')
    working=facts.get('condition')=='working'
    repairable=facts.get('condition')=='repairable'
    cost_ok=float(facts.get('repair_cost',0)) <= float(facts.get('replacement_cost',0))*0.5 if float(facts.get('replacement_cost',0))>0 else False
    return {"facts":{"special_handling_required":hazardous,"may_qualify_for_reuse":working,"may_qualify_for_repair":repairable and cost_ok},"explanation":"Hazardous items take priority for special handling. Working devices may qualify for reuse. Repairable devices qualify under this example when estimated repair cost is at most half of replacement cost."}
