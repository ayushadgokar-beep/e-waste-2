from .reflex_agent import choose_action


def next_action(device, history=None):
    history=list(history or [])
    if history and history[-1] in ('repaired','repair_failed'):
        return {'action':'quality_check' if history[-1]=='repaired' else 'recover_components','internal_state':{'history':history,'previous_outcome':history[-1]},'explanation':'The stored processing outcome changes the next action.'}
    action=choose_action(device)
    return {'action':action,'internal_state':{'history':history,'previous_outcome':None},'explanation':'With no prior outcome, the agent selects an action from the current device observation.'}
