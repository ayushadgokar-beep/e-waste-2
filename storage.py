"""Small JSON file store with safe replacement writes and validation."""
import json
import os
import tempfile
from pathlib import Path

BASE_DIR=Path(__file__).resolve().parent
DATA_DIR=BASE_DIR/'data'
DEFAULTS={
 'devices': [], 'jobs': [],
 'locations': {'locations':['North Hub','Central Hub','South Hub','East Depot'],'edges':[['North Hub','Central Hub',4],['Central Hub','South Hub',3],['North Hub','East Depot',5],['East Depot','South Hub',2],['Central Hub','East Depot',2]]},
 'benches': [{'id':'repair-1','name':'Repair Bench','types':['repair','reuse'],'hazardous':False},{'id':'recovery-1','name':'Recovery Station','types':['recover'],'hazardous':False},{'id':'safe-1','name':'Hazardous Handling Station','types':['recycle','special_handling'],'hazardous':True}],
 'settings': {'repair_ratio':0.5,'reuse_max_age':5,'sample_only':True},
}


def ensure_data():
    DATA_DIR.mkdir(parents=True,exist_ok=True)
    for name,value in DEFAULTS.items():
        path=DATA_DIR/f'{name}.json'
        if not path.exists(): write_json(path,value)


def read_json(path, default=None):
    try:
        with open(path,encoding='utf-8') as f: return json.load(f)
    except FileNotFoundError:
        if default is not None: return default
        raise
    except (json.JSONDecodeError,UnicodeDecodeError) as exc:
        raise ValueError(f'Invalid JSON in {Path(path).name}') from exc


def write_json(path, value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(value,f,indent=2,ensure_ascii=False); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def load(name): return read_json(DATA_DIR/f'{name}.json',DEFAULTS[name])
def save(name,value): write_json(DATA_DIR/f'{name}.json',value)
