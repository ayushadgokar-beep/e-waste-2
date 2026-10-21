from flask import Flask, jsonify, render_template, request
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
import logging
import math
import re
from werkzeug.exceptions import HTTPException
from storage import ensure_data, load, save, BASE_DIR
from recommendations import recommend
from algorithms import graph_search, state_space, constraint_solver, propositional_logic, unification, reflex_agent, model_based_agent, minimax, alpha_beta

app=Flask(__name__)
app.config.update(JSON_SORT_KEYS=False,MAX_CONTENT_LENGTH=64*1024)
logging.basicConfig(level=logging.INFO)
ensure_data()
CATEGORIES={'mobile','laptop','computer','battery','television','appliance','other'}
CONDITIONS={'working','repairable','damaged','hazardous'}
RECOMMENDATION_JOB_TYPES={
    'repair':'repair',
    'reuse or donate':'reuse',
    'recover components':'recover',
    'authorized recycling':'recycle',
    'special handling':'special_handling',
}
FINAL_DEVICE_STATUSES={'completed','recycled'}


def ok(data,status=200): return jsonify({'success':True,'data':data}),status
def fail(message,status=400): return jsonify({'success':False,'error':message}),status


@app.errorhandler(413)
def too_large(_): return fail('Request body is too large.',413)
@app.errorhandler(Exception)
def unexpected(exc):
    if isinstance(exc, (KeyboardInterrupt,SystemExit)): raise exc
    if isinstance(exc, HTTPException): return fail(exc.description,exc.code or 500)
    app.logger.exception('Request failed')
    return fail('The request could not be completed. Check the submitted values and stored data.',500)


def device_payload(data, partial=False):
    if not isinstance(data,dict): raise ValueError('Request body must be a JSON object.')
    fields={'name':str,'category':str,'condition':str,'age':int,'repair_cost':float,'replacement_cost':float,'location':str,'weight':float,'battery_present':bool,'notes':str}
    out={}
    for key,typ in fields.items():
        if key not in data:
            if partial: continue
            if key in ('notes','battery_present'): out[key]='' if key=='notes' else False
            else: raise ValueError(f'{key.replace("_"," ").capitalize()} is required.')
        if key in data:
            val=data[key]
            if typ in (int,float):
                if isinstance(val,bool): raise ValueError(f'{key.replace("_"," ").capitalize()} must be numeric.')
                try: num=float(val)
                except (TypeError,ValueError): raise ValueError(f'{key.replace("_"," ").capitalize()} must be numeric.')
                if not math.isfinite(num) or num<0 or (typ is int and not num.is_integer()): raise ValueError(f'{key.replace("_"," ").capitalize()} must be a valid non-negative number.')
                val=int(num) if typ is int else num
            elif typ is bool:
                if not isinstance(val,bool): raise ValueError('Battery present must be true or false.')
            else:
                if not isinstance(val,str): raise ValueError(f'{key.replace("_"," ").capitalize()} must be text.')
                val=val.strip()
                if key in ('name','location','condition','category') and not val: raise ValueError(f'{key.replace("_"," ").capitalize()} cannot be empty.')
            out[key]=val
    if 'category' in out and out['category'] not in CATEGORIES: raise ValueError('Choose a listed device category.')
    if 'condition' in out and out['condition'] not in CONDITIONS: raise ValueError('Choose a listed device condition.')
    return out


def processing_stage(device, settings):
    decision=recommend(device,settings)['recommendation']
    return RECOMMENDATION_JOB_TYPES[decision],decision=='special handling'


def clear_job_assignment(job):
    for key in ('resource_id','resource_name','slot'):
        job.pop(key,None)


def ensure_processing_job(device, jobs, settings, duration=1):
    """Create or update the one active job that represents this device's next stage."""
    if device.get('status') in FINAL_DEVICE_STATUSES:
        return None,False,0
    kind,hazardous=processing_stage(device,settings)
    active=[job for job in jobs if job.get('device_id')==device['id'] and job.get('status')!='complete']
    keeper=next((job for job in active if job.get('type')==kind),active[0] if active else None)
    if keeper is None:
        keeper={'id':str(uuid4()),'device_id':device['id'],'device_name':device['name'],
                'type':kind,'duration':duration,'hazardous':hazardous,'status':'pending'}
        jobs.append(keeper)
        return keeper,True,0
    changed=False
    if keeper.get('type')!=kind or keeper.get('hazardous')!=hazardous:
        keeper['type']=kind; keeper['hazardous']=hazardous; keeper['status']='pending'
        clear_job_assignment(keeper); changed=True
    if keeper.get('device_name')!=device['name']:
        keeper['device_name']=device['name']; changed=True
    duplicate_ids={id(job) for job in active if job is not keeper}
    removed=sum(1 for job in jobs if id(job) in duplicate_ids)
    if removed:
        jobs[:]=[job for job in jobs if id(job) not in duplicate_ids]
        changed=True
    return keeper,changed,removed


def sync_eligible_device_jobs(devices, jobs, settings):
    created=updated=duplicates_removed=0
    for device in devices:
        if device.get('status') not in {'registered','collected','processing'}:
            continue
        previous_ids={id(job) for job in jobs}
        job,changed,removed=ensure_processing_job(device,jobs,settings)
        is_new=job is not None and id(job) not in previous_ids
        if device.get('status')=='processing' and not (
            job and job.get('status')=='scheduled' and job.get('resource_id') and
            isinstance(job.get('slot'),int)
        ):
            device['status']='collected'; changed=True
        created+=int(is_new)
        updated+=int(changed and not is_new)
        duplicates_removed+=removed
    return created,updated,duplicates_removed


def update_device_jobs_for_status(device, jobs, new_status, settings):
    if new_status in FINAL_DEVICE_STATUSES:
        for job in jobs:
            if job.get('device_id')==device['id'] and job.get('status')!='complete':
                job['status']='complete'
        return
    if new_status in {'registered','collected'}:
        for job in jobs:
            if job.get('device_id')==device['id'] and job.get('status')!='complete':
                job['status']='pending'; clear_job_assignment(job)
        ensure_processing_job(device,jobs,settings)


def persist_schedule(jobs, devices, benches):
    result=constraint_solver.schedule_jobs(jobs,benches)
    device_by_id={device['id']:device for device in devices if device.get('id')}
    assignments={item['job_id']:item for item in result.get('assignments',[])}
    if result['success']:
        for job in jobs:
            assignment=assignments.get(job.get('id'))
            if not assignment:
                continue
            job.update(status='scheduled',resource_id=assignment['bench_id'],
                       resource_name=assignment['bench'],slot=assignment['slot'],
                       duration=assignment['duration'])
            device=device_by_id.get(job.get('device_id'))
            if device and device.get('status') not in FINAL_DEVICE_STATUSES:
                device['status']='processing'
    else:
        active_device_ids=set()
        for job in jobs:
            if job.get('status') in {'pending','scheduled'}:
                job['status']='pending'; clear_job_assignment(job)
                active_device_ids.add(job.get('device_id'))
        for device_id in active_device_ids:
            device=device_by_id.get(device_id)
            if device and device.get('status')=='processing':
                device['status']='collected'
    save('jobs',jobs)
    save('devices',devices)
    return result


@app.get('/')
def index(): return render_template('index.html')
@app.get('/favicon.ico')
def favicon(): return '',204


@app.get('/api/dashboard')
def dashboard():
    devices=load('devices'); jobs=load('jobs')
    recs=[recommend(d,load('settings')) for d in devices]
    cats={c:sum(1 for d in devices if d['category']==c) for c in sorted(CATEGORIES) if any(d['category']==c for d in devices)}
    return ok({'total_devices':len(devices),'pending_jobs':sum(j.get('status')=='pending' for j in jobs),'repair_reuse':sum(r['recommendation'] in ('repair','reuse or donate') for r in recs),'awaiting_recycling':sum(r['recommendation'] in ('authorized recycling','special handling') for r in recs),'job_status':{s:sum(j.get('status')==s for j in jobs) for s in ('pending','scheduled','complete')},'categories':cats,'recent':sorted(devices,key=lambda d:d.get('created_at',''),reverse=True)[:5]})


@app.route('/api/devices',methods=['GET','POST'])
def devices_api():
    devices=load('devices')
    if request.method=='GET':
        q=request.args.get('q','').lower(); cat=request.args.get('category'); status=request.args.get('status')
        filtered=[d for d in devices if (not q or q in d['name'].lower() or q in d['location'].lower() or q in d['id'].lower()) and (not cat or d['category']==cat) and (not status or d['status']==status)]
        return ok(filtered)
    try: item=device_payload(request.get_json(silent=True))
    except ValueError as exc: return fail(str(exc))
    locs=load('locations')['locations']
    if item['location'] not in locs: return fail('Choose a collection location from the sample location list.')
    item.update(id=str(uuid4()),status='registered',created_at=datetime.now(timezone.utc).isoformat())
    devices.append(item); save('devices',devices)
    jobs=load('jobs'); ensure_processing_job(item,jobs,load('settings')); save('jobs',jobs)
    return ok(item,201)


@app.route('/api/devices/<device_id>',methods=['GET','PUT'])
def device_api(device_id):
    devices=load('devices'); idx=next((i for i,d in enumerate(devices) if d['id']==device_id),None)
    if idx is None: return fail('Device not found.',404)
    if request.method=='GET': return ok(devices[idx])
    body=request.get_json(silent=True)
    if not isinstance(body,dict): return fail('Request body must be a JSON object.')
    if set(body)=={'status'}:
        if body['status'] not in {'registered','collected','processing','completed','recycled'}:
            return fail('Choose a listed device status.')
        jobs=load('jobs'); status=body['status']; device=devices[idx]
        if status=='processing' and not any(
            job.get('device_id')==device_id and job.get('status')=='scheduled' and
            job.get('resource_id') and isinstance(job.get('slot'),int) for job in jobs
        ):
            return fail('Run the scheduler to assign a compatible resource and time slot before marking a device as processing.',409)
        device['status']=status
        update_device_jobs_for_status(device,jobs,status,load('settings'))
        save('devices',devices); save('jobs',jobs)
        return ok(device)
    try: changes=device_payload(body,partial=True)
    except ValueError as exc: return fail(str(exc))
    devices[idx].update(changes); save('devices',devices)
    jobs=load('jobs')
    if devices[idx].get('status') in {'registered','collected','processing'}:
        ensure_processing_job(devices[idx],jobs,load('settings')); save('jobs',jobs)
    return ok(devices[idx])


@app.get('/api/recommendations')
def recommendations_api(): return ok([dict(id=d['id'],name=d['name'],**recommend(d,load('settings'))) for d in load('devices')])
@app.post('/api/recommendations/<device_id>')
def recommendation_api(device_id):
    item=next((d for d in load('devices') if d['id']==device_id),None)
    return fail('Device not found.',404) if item is None else ok(recommend(item,load('settings')))
@app.get('/api/locations')
def locations_api(): return ok(load('locations'))


def route_graph(locations):
    graph={node:{} for node in locations['locations']}
    for a,b,cost in locations['edges']:
        graph[a][b]=graph[b][a]=cost
    return graph


def run_route(graph, start, goal, algorithm):
    heuristic={node:0 for node in graph} # zero is admissible for these non-negative simulated costs
    methods={'bfs':lambda:graph_search.bfs(graph,start,goal),
             'dfs':lambda:graph_search.dfs(graph,start,goal),
             'greedy':lambda:graph_search.greedy_best_first(graph,start,goal,heuristic),
             'astar':lambda:graph_search.astar(graph,start,goal,heuristic)}
    result=methods[algorithm]()
    result.update({'algorithm':algorithm,'start':start,'goal':goal,
                   'success':bool(result['path']),'nodes_visited':len(result['visited']),
                   'route_edges':max(0,len(result['path'])-1),
                   'unit':'simulated cost units',
                   'note':'Simulated network costs only; not distance, travel time, or fuel cost.'})
    if algorithm=='astar':
        result['evaluation']='f(n) = g(n) + h(n); this demonstration uses h(n)=0, an admissible heuristic.'
    return result


def route_request(data, locations):
    if not isinstance(data,dict):
        return None,'Request body must be a JSON object.'
    start=data.get('start'); goal=data.get('goal'); algorithm=data.get('algorithm','astar')
    if start not in locations['locations'] or goal not in locations['locations']:
        return None,'Select valid sample start and destination locations.'
    if algorithm not in {'bfs','dfs','greedy','astar'}:
        return None,'Choose bfs, dfs, greedy, or astar.'
    return run_route(route_graph(locations),start,goal,algorithm),None


@app.post('/api/routes')
def route_api():
    result,error=route_request(request.get_json(silent=True),load('locations'))
    return fail(error) if error else ok(result)


@app.post('/api/routes/compare')
def route_compare_api():
    data=request.get_json(silent=True); locations=load('locations')
    if not isinstance(data,dict): return fail('Request body must be a JSON object.')
    start=data.get('start'); goal=data.get('goal')
    if start not in locations['locations'] or goal not in locations['locations']:
        return fail('Select valid sample start and destination locations.')
    graph=route_graph(locations)
    results=[run_route(graph,start,goal,algorithm) for algorithm in ('bfs','dfs','greedy','astar')]
    return ok({'start':start,'goal':goal,'results':results,'execution_time':'Not measured on this small demonstration graph.'})


@app.route('/api/jobs',methods=['GET','POST','DELETE'])
def jobs_api():
    jobs=load('jobs')
    if request.method=='GET': return ok(jobs)
    if request.method=='DELETE':
        devices=load('devices')
        assigned_device_ids={job.get('device_id') for job in jobs if job.get('status')=='scheduled'}
        for device in devices:
            if device.get('id') in assigned_device_ids and device.get('status')=='processing':
                device['status']='collected'
        save('jobs',[])
        save('devices',devices)
        return ok({'deleted':len(jobs)})
    data=request.get_json(silent=True)
    if not isinstance(data,dict): return fail('Request body must be a JSON object.')
    try:
        device_id=str(data['device_id']); kind=str(data['type']); raw_duration=data.get('duration',1); status=data.get('status','pending')
    except (KeyError,ValueError,TypeError): return fail('device_id and a valid processing type are required.')
    if isinstance(raw_duration,bool): return fail('Duration must be a positive whole number of slots.')
    try: duration_value=float(raw_duration)
    except (TypeError,ValueError): return fail('Duration must be a positive whole number of slots.')
    if not math.isfinite(duration_value) or duration_value<1 or not duration_value.is_integer(): return fail('Duration must be a positive whole number of slots.')
    duration=int(duration_value)
    device=next((d for d in load('devices') if d['id']==device_id),None)
    if not device: return fail('Device not found.',404)
    if device.get('status') in FINAL_DEVICE_STATUSES: return fail('A completed or recycled device cannot be queued for processing.',409)
    expected_kind,hazardous=processing_stage(device,load('settings'))
    if kind!=expected_kind or status!='pending': return fail('The processing type must match the device recommendation and new jobs must be pending.')
    job,changed,_=ensure_processing_job(device,jobs,load('settings'),duration)
    if job is None: return fail('Device is not eligible for processing.',409)
    if job.get('status')!='scheduled': job['duration']=duration
    save('jobs',jobs)
    return ok(job,200 if not changed else 201)


@app.post('/api/jobs/sync')
def sync_jobs_api():
    devices=load('devices'); jobs=load('jobs')
    created,updated,duplicates_removed=sync_eligible_device_jobs(devices,jobs,load('settings'))
    if created or updated or duplicates_removed:
        save('jobs',jobs); save('devices',devices)
    return ok({'created':created,'updated':updated,'duplicates_removed':duplicates_removed,'jobs':jobs})


@app.post('/api/schedule')
def schedule_api(): return ok(persist_schedule(load('jobs'),load('devices'),load('benches')))


@app.post('/api/ai/<concept>')
def ai_api(concept):
    data=request.get_json(silent=True) or {}
    if concept=='state-space': return ok(state_space.processing_plan(data.get('start','unprocessed'),data.get('goal','special_handling')))
    if concept in ('bfs','dfs','greedy','astar'):
        locations=load('locations'); graph={n:{} for n in locations['locations']}
        for a,b,cost in locations['edges']: graph[a][b]=graph[b][a]=cost
        start=data.get('start',locations['locations'][0]); goal=data.get('goal',locations['locations'][-1])
        if start not in graph or goal not in graph: return fail('Select valid sample locations.')
        heuristic={n:0 for n in graph}
        fn={'bfs':graph_search.bfs,'dfs':graph_search.dfs,'greedy':graph_search.greedy_best_first,'astar':graph_search.astar}[concept]
        result=fn(graph,start,goal) if concept in ('bfs','dfs') else fn(graph,start,goal,heuristic)
        result['unit']='sample distance units'; return ok(result)
    if concept=='min-conflicts': return ok(constraint_solver.schedule_jobs(data.get('jobs',[{'id':'job-a','type':'repair'},{'id':'job-b','type':'repair'}]),load('benches'),seed=3))
    if concept=='propositional-logic': return ok(propositional_logic.evaluate(data))
    if concept=='unification':
        try: result=unification.unify(unification.parse_term(data.get('left','process(?x, battery)')),unification.parse_term(data.get('right','process(phone, battery)')))
        except ValueError as exc: return fail(str(exc))
        return ok(result)
    if concept=='reflex-agent': return ok({'action':reflex_agent.choose_action(data),'explanation':'Action uses only the current observation.'})
    if concept=='model-based-agent': return ok(model_based_agent.next_action(data,data.get('history',[])))
    if concept=='minimax': return ok(minimax.minimax())
    if concept=='alpha-beta': return ok(alpha_beta.alpha_beta())
    return fail('Unknown AI concept.',404)


if __name__=='__main__': app.run(debug=False)
