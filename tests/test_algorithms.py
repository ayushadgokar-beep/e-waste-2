from algorithms.graph_search import bfs, dfs, greedy_best_first, astar
from algorithms.constraint_solver import schedule_jobs
from algorithms.propositional_logic import evaluate
from algorithms.unification import unify, parse_term
from algorithms.reflex_agent import choose_action
from algorithms.model_based_agent import next_action
from algorithms.minimax import minimax
from algorithms.alpha_beta import alpha_beta
from algorithms.state_space import processing_plan

GRAPH={'a':{'b':2,'c':1},'b':{'a':2,'d':2},'c':{'a':1,'d':4},'d':{'b':2,'c':4}}
BENCHES=[{'id':'b1','name':'Bench','types':['repair'],'hazardous':False},{'id':'safe','name':'Safe','types':['special_handling'],'hazardous':True}]

def test_graph_algorithms_find_paths():
    assert bfs(GRAPH,'a','d')['path'][0]=='a'
    assert dfs(GRAPH,'a','d')['path'][-1]=='d'
    assert astar(GRAPH,'a','d',{'a':0,'b':0,'c':0,'d':0})['cost']==4
    assert greedy_best_first(GRAPH,'a','d',{'a':2,'b':1,'c':1,'d':0})['path']

def test_graph_unreachable():
    assert bfs({'a':{},'b':{}},'a','b')['path']==[]

def test_route_trace_matches_real_search_order_and_edges():
    for result in (bfs(GRAPH,'a','d'),dfs(GRAPH,'a','d'),
                   greedy_best_first(GRAPH,'a','d',{'a':2,'b':1,'c':1,'d':0}),
                   astar(GRAPH,'a','d',{'a':0,'b':0,'c':0,'d':0})):
        assert [step['node'] for step in result['steps']]==result['visited']
        assert result['path'][0]=='a' and result['path'][-1]=='d'
        assert result['cost']==sum(GRAPH[a][b] for a,b in zip(result['path'],result['path'][1:]))
        assert all(b in GRAPH[a] for a,b in result['explored_edges'])

def test_route_trace_handles_same_node_and_unreachable_goal():
    same=bfs(GRAPH,'a','a')
    unreachable=astar({'a':{},'b':{}},'a','b',{'a':0,'b':0})
    assert same['path']==['a'] and same['cost']==0 and same['steps']==[{'step':1,'node':'a','event':'expanded'}]
    assert unreachable['path']==[] and unreachable['cost'] is None

def test_scheduler_hazard_compatibility():
    jobs=[{'id':'j1','type':'repair','hazardous':False},{'id':'j2','type':'special_handling','hazardous':True}]
    result=schedule_jobs(jobs,BENCHES)
    assert result['success'] and result['conflicts']==0
    assigned={x['job_id']:x['bench_id'] for x in result['assignments']}
    assert assigned=={'j1':'b1','j2':'safe'}

def test_scheduler_reports_impossible_domain():
    result=schedule_jobs([{'id':'j','type':'repair','hazardous':True}],BENCHES)
    assert not result['success'] and result['assignments']==[]
    assert result['unsatisfied'][0]['job_id']=='j'

def test_scheduler_places_jobs_in_multiple_nonconflicting_slots():
    jobs=[{'id':f'j{i}','type':'repair','duration':1} for i in range(4)]
    result=schedule_jobs(jobs,[{'id':'only','name':'Only bench','types':['repair']}])
    assert result['success'] and result['conflicts']==0
    slots=[item['slot'] for item in result['assignments']]
    assert len(set(slots))==4

def test_scheduler_accounts_for_job_duration():
    jobs=[{'id':'long','type':'repair','duration':2},{'id':'short','type':'repair','duration':1}]
    result=schedule_jobs(jobs,[{'id':'only','name':'Only bench','types':['repair']}])
    by_id={item['job_id']:item for item in result['assignments']}
    assert result['success'] and result['conflicts']==0
    assert by_id['long']['slot']+by_id['long']['duration'] <= by_id['short']['slot'] or by_id['short']['slot']+by_id['short']['duration'] <= by_id['long']['slot']

def test_scheduler_reports_unsatisfiable_slot_domains():
    jobs=[{'id':'j1','type':'repair','available_slots':[0]},{'id':'j2','type':'repair','available_slots':[0]}]
    result=schedule_jobs(jobs,[{'id':'only','name':'Only bench','types':['repair']}])
    assert not result['success'] and result['assignments']==[]
    assert result['unsatisfied'] and 'conflicts' in result['unsatisfied'][0]['reason']

def test_scheduler_rejects_invalid_duration_and_status():
    bench=[{'id':'b','name':'Bench','types':['repair']}]
    assert not schedule_jobs([{'id':'bad-duration','type':'repair','duration':0}],bench)['success']
    assert not schedule_jobs([{'id':'bad-status','type':'repair','status':'waiting'}],bench)['success']

def test_logic_and_agents():
    assert evaluate({'condition':'hazardous'})['facts']['special_handling_required']
    assert choose_action({'condition':'working'})=='reuse_or_donate'
    assert next_action({'condition':'repairable'},['repaired'])['action']=='quality_check'

def test_unification_and_occurs_check():
    assert unify(parse_term('f(?x, battery)'),parse_term('f(phone, battery)'))['substitutions']=={'?x':'phone'}
    assert not unify(parse_term('?x'),parse_term('f(?x)'))['success']
    assert not unify(parse_term('phone'),parse_term('battery'))['success']

def test_minimax_and_alpha_beta_agree():
    assert (minimax()['move'],minimax()['utility'])==(alpha_beta()['move'],alpha_beta()['utility'])
    assert alpha_beta()['pruned']>0

def test_state_space_plan():
    result=processing_plan(goal='special_handling')
    assert result['path']==['unprocessed','inspected','special_handling']
