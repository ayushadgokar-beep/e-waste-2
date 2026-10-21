import pytest
import app as application
from storage import DEFAULTS
from pathlib import Path

@pytest.fixture
def client(tmp_path,monkeypatch):
    import storage
    monkeypatch.setattr(storage,'DATA_DIR',tmp_path)
    storage.ensure_data()
    monkeypatch.setattr(application,'load',storage.load)
    monkeypatch.setattr(application,'save',storage.save)
    return application.app.test_client()

def payload(**overrides):
    data={'name':'Test phone','category':'mobile','condition':'working','age':1,'repair_cost':0,'replacement_cost':100,'location':'North Hub','weight':0.2,'battery_present':True,'notes':''};data.update(overrides);return data

def test_device_registration_and_dashboard(client):
    response=client.post('/api/devices',json=payload())
    assert response.status_code==201
    body=response.get_json()['data'];assert body['id']
    jobs=client.get('/api/jobs').get_json()['data']
    assert len(jobs)==1 and jobs[0]['device_id']==body['id'] and jobs[0]['type']=='reuse'
    assert client.get('/api/dashboard').get_json()['data']['total_devices']==1
    assert client.get('/api/dashboard').get_json()['data']['pending_jobs']==1
    assert client.post('/api/jobs',json={'device_id':body['id'],'type':'repair','duration':1.5}).status_code==400

def test_registration_creates_hazard_safe_job_and_duplicate_requests_are_idempotent(client):
    device=client.post('/api/devices',json=payload(condition='hazardous',category='battery')).get_json()['data']
    jobs=client.get('/api/jobs').get_json()['data']
    assert len(jobs)==1
    job=jobs[0]
    assert job['device_id']==device['id'] and job['type']=='special_handling' and job['hazardous']
    duplicate=client.post('/api/jobs',json={'device_id':device['id'],'type':'special_handling'})
    assert duplicate.status_code==200 and duplicate.get_json()['data']['id']==job['id']
    scheduled=client.post('/api/schedule',json={}).get_json()['data']
    assert scheduled['success'] and scheduled['assignments'][0]['bench_id']=='safe-1'
    stored=client.get('/api/jobs').get_json()['data'][0]
    assert stored['status']=='scheduled' and stored['resource_id']=='safe-1'
    assert stored['slot']==scheduled['assignments'][0]['slot']

def test_status_updates_preserve_one_linked_job_and_complete_it(client):
    device=client.post('/api/devices',json=payload()).get_json()['data']
    original=client.get('/api/jobs').get_json()['data'][0]
    assert client.put('/api/devices/'+device['id'],json={'status':'collected'}).status_code==200
    assert client.get('/api/jobs').get_json()['data'][0]['id']==original['id']
    result=client.post('/api/schedule',json={}).get_json()['data']
    assert result['success'] and result['assignments'][0]['job_id']==original['id']
    assert client.get('/api/devices/'+device['id']).get_json()['data']['status']=='processing'
    assert client.put('/api/devices/'+device['id'],json={'status':'completed'}).status_code==200
    completed=client.get('/api/jobs').get_json()['data'][0]
    assert completed['id']==original['id'] and completed['status']=='complete'
    assert client.get('/api/dashboard').get_json()['data']['job_status']['complete']==1
    client.delete('/api/jobs')
    assert client.put('/api/devices/'+device['id'],json={'status':'collected'}).status_code==200
    requeued=client.get('/api/jobs').get_json()['data']
    assert len(requeued)==1 and requeued[0]['device_id']==device['id'] and requeued[0]['status']=='pending'

def test_explicit_job_sync_repairs_duplicates_without_page_load_side_effects(client):
    import storage
    device=client.post('/api/devices',json=payload()).get_json()['data']
    first=client.get('/api/jobs').get_json()['data'][0]
    duplicate=dict(first,id='duplicate-job')
    storage.save('jobs',[first,duplicate])
    assert len(client.get('/api/jobs').get_json()['data'])==2
    result=client.post('/api/jobs/sync',json={}).get_json()['data']
    assert result['duplicates_removed']==1
    jobs=client.get('/api/jobs').get_json()['data']
    assert len(jobs)==1 and jobs[0]['device_id']==device['id'] and jobs[0]['id']==first['id']

def test_deleting_scheduled_jobs_preserves_devices_and_removes_processing_state(client):
    import storage
    device=client.post('/api/devices',json=payload()).get_json()['data']
    unrelated=dict(device,id='unrelated-device',name='Unrelated device',status='processing')
    storage.save('devices',[device,unrelated])
    assert client.post('/api/schedule',json={}).get_json()['data']['success']
    assert client.get('/api/devices/'+device['id']).get_json()['data']['status']=='processing'
    deleted=client.delete('/api/jobs').get_json()['data']
    assert deleted['deleted']==1
    assert client.get('/api/jobs').get_json()['data']==[]
    preserved=client.get('/api/devices/'+device['id']).get_json()['data']
    assert preserved['id']==device['id'] and preserved['status']=='collected'
    assert client.get('/api/devices/unrelated-device').get_json()['data']['status']=='processing'

def test_validation_and_missing_device(client):
    assert client.post('/api/devices',json=payload(age=-1)).status_code==400
    assert client.get('/api/devices/no-such-id').status_code==404
    assert client.post('/api/devices',data='not-json',content_type='application/json').status_code==400
    assert client.get('/unknown-page').status_code==404

def test_recommendation_and_route(client):
    client.post('/api/devices',json=payload(condition='damaged',notes='battery is swollen'))
    devices=client.get('/api/devices').get_json()['data']
    assert client.post('/api/recommendations/'+devices[0]['id'],json={}).get_json()['data']['recommendation']=='special handling'
    route=client.post('/api/routes',json={'start':'North Hub','goal':'South Hub','algorithm':'astar'})
    assert route.status_code==200 and route.get_json()['data']['path'][0]=='North Hub'

def test_route_api_algorithms_trace_cost_and_endpoint_variation(client):
    locations=client.get('/api/locations').get_json()['data']
    weights={node:{} for node in locations['locations']}
    for a,b,cost in locations['edges']:
        weights[a][b]=weights[b][a]=cost
    for algorithm in ('bfs','dfs','greedy','astar'):
        for start,goal in (('North Hub','South Hub'),('East Depot','Central Hub')):
            response=client.post('/api/routes',json={'start':start,'goal':goal,'algorithm':algorithm})
            assert response.status_code==200
            result=response.get_json()['data']
            assert result['success'] and result['algorithm']==algorithm
            assert result['start']==start and result['goal']==goal
            assert result['path'][0]==start and result['path'][-1]==goal
            assert result['nodes_visited']==len(result['visited'])
            assert result['route_edges']==len(result['path'])-1
            assert result['steps']==[{'step':i,'node':node,'event':'expanded'} for i,node in enumerate(result['visited'],1)]
            assert result['cost']==sum(weights[a][b] for a,b in zip(result['path'],result['path'][1:]))
            assert all(b in weights[a] for a,b in result['explored_edges'])

def test_route_api_validates_algorithms_and_unreachable_graph(client):
    import storage
    assert client.post('/api/routes',json={'start':'Mars','goal':'South Hub','algorithm':'bfs'}).status_code==400
    assert client.post('/api/routes',json={'start':'North Hub','goal':'South Hub','algorithm':'quantum'}).status_code==400
    storage.save('locations',{'locations':['North Hub','South Hub'],'edges':[]})
    result=client.post('/api/routes',json={'start':'North Hub','goal':'South Hub','algorithm':'astar'}).get_json()['data']
    assert not result['success'] and result['path']==[] and result['cost'] is None
    assert result['nodes_visited']==1 and result['route_edges']==0

def test_route_comparison_returns_real_algorithm_results(client):
    response=client.post('/api/routes/compare',json={'start':'North Hub','goal':'South Hub'})
    assert response.status_code==200
    result=response.get_json()['data']
    assert [r['algorithm'] for r in result['results']]==['bfs','dfs','greedy','astar']
    assert all(r['success'] and r['path'][0]=='North Hub' and r['path'][-1]=='South Hub' for r in result['results'])
    assert result['execution_time']=='Not measured on this small demonstration graph.'
    assert client.post('/api/routes/compare',json={'start':'North Hub','goal':'missing'}).status_code==400

def test_route_page_has_visualization_controls_and_backend_wiring():
    root=Path(__file__).resolve().parents[1]
    markup=(root/'templates'/'index.html').read_text(encoding='utf-8')
    script=(root/'static'/'js'/'app.js').read_text(encoding='utf-8')
    for control in ('route-map','map-world','route-start','route-goal','route-algorithm','route-find',
                    'route-play','route-pause','route-animation-reset','route-compare','route-timeline'):
        assert f'id="{control}"' in markup
    assert "api('/api/routes'" in script and "api('/api/routes/compare'" in script
    assert "setInterval(()=>{truckProgress" in script and "route-animation-reset').onclick" in script
    assert "route-comparison-rows').innerHTML=comparison.results.map" in script

def test_ai_endpoints(client):
    for concept in ['state-space','bfs','dfs','greedy','astar','min-conflicts','propositional-logic','unification','reflex-agent','model-based-agent','minimax','alpha-beta']:
        assert client.post('/api/ai/'+concept,json={}).status_code==200
    assert client.post('/api/ai/missing',json={}).status_code==404

def test_schedule_api_returns_valid_multi_slot_assignments(client):
    import storage
    jobs=[{'id':f'job-{i}','type':'repair','duration':1,'status':'pending'} for i in range(3)]
    benches=[{'id':'repair-1','name':'Repair Bench','types':['repair'],'hazardous':False}]
    storage.save('jobs',jobs); storage.save('benches',benches)
    result=client.post('/api/schedule',json={}).get_json()['data']
    assert result['success'] and result['conflicts']==0
    assert {item['job_id'] for item in result['assignments']}=={item['id'] for item in jobs}
    assert len({item['slot'] for item in result['assignments']})==3

def test_schedule_api_explains_impossible_assignments(client):
    import storage
    storage.save('jobs',[{'id':'unsafe-repair','type':'repair','hazardous':True,'duration':1,'status':'pending'}])
    storage.save('benches',[{'id':'repair-1','name':'Repair Bench','types':['repair'],'hazardous':False}])
    result=client.post('/api/schedule',json={}).get_json()['data']
    assert not result['success'] and result['assignments']==[]
    assert result['unsatisfied'][0]['job_id']=='unsafe-repair'

def test_delete_all_jobs_preserves_unrelated_data_and_clears_schedule(client):
    import storage
    devices=[dict(payload(name='Saved device'),id='device-1',status='registered')]
    jobs=[{'id':'job-1','device_id':'device-1','device_name':'Saved device','type':'repair','duration':1,'status':'pending'},
          {'id':'job-2','device_id':'device-1','device_name':'Saved device','type':'reuse','duration':1,'status':'scheduled'}]
    unrelated={name:storage.load(name) for name in ('locations','benches','settings')}
    storage.save('devices',devices)
    storage.save('jobs',jobs)
    deleted=client.delete('/api/jobs')
    assert deleted.status_code==200
    assert deleted.get_json()['data']=={'deleted':2}
    assert client.get('/api/jobs').get_json()['data']==[]
    assert storage.load('devices')==devices
    assert {name:storage.load(name) for name in unrelated}==unrelated
    assert client.get('/api/dashboard').get_json()['data']['pending_jobs']==0
    schedule=client.post('/api/schedule',json={}).get_json()['data']
    assert schedule['success'] and schedule['assignments']==[] and schedule['conflicts']==0

def test_delete_all_jobs_handles_empty_store(client):
    import storage
    assert storage.load('jobs')==[]
    response=client.delete('/api/jobs')
    assert response.status_code==200
    assert response.get_json()['data']=={'deleted':0}
    assert client.get('/api/jobs').get_json()['data']==[]
