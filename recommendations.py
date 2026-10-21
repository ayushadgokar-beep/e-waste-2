def recommend(device, settings):
    condition=device['condition']; age=device['age']; ratio=settings.get('repair_ratio',0.5)
    notes=device.get('notes','').lower()
    battery_risk=device.get('battery_present') and (condition in ('damaged','hazardous') or any(word in notes for word in ('swollen','leaking','overheating','punctured')))
    if condition=='hazardous' or battery_risk: choice='special handling'; reason='The item is marked hazardous or has a potentially unsafe battery; it requires designated authorized handling.'
    elif condition=='working' and age<=settings.get('reuse_max_age',5): choice='reuse or donate'; reason='The device is working and within the example reuse age threshold.'
    elif condition=='repairable' and device['repair_cost']<=device['replacement_cost']*ratio: choice='repair'; reason=f"Estimated repair cost is at most {ratio:.0%} of replacement cost."
    elif condition=='damaged' or condition=='repairable': choice='recover components'; reason='Repair is not selected by the configured cost rule; recover components through a suitable processing station.'
    else: choice='authorized recycling'; reason='The device does not meet the example reuse or repair rules.'
    return {'recommendation':choice,'reason':reason,'safety_note':'Educational preliminary guidance only. Hazardous batteries require authorized special handling; do not dismantle or place in household waste.' if choice=='special handling' or device.get('battery_present') else 'Educational preliminary guidance only; not professional safety certification.'}
