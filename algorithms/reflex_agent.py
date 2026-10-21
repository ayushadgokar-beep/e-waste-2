def choose_action(device):
    notes=str(device.get('notes','')).lower()
    if device.get('condition')=='hazardous' or (device.get('battery_present') and (device.get('condition')=='damaged' or any(word in notes for word in ('swollen','leaking','overheating','punctured')))): return 'special_handling'
    if device.get('condition')=='working': return 'reuse_or_donate'
    if device.get('condition')=='repairable': return 'repair_assessment'
    return 'authorized_recycling'
