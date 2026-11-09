"""Plugin explícito: python -m pytest -p testing.pytest_inventory ...

El directorio scripts/crea debe estar disponible en sys.path por la entrada
revisada (run_pytest.py). No se instala ni registra globalmente.
"""
import hashlib
import json
import os
from pathlib import Path
import pytest

def pytest_addoption(parser):
    parser.addoption('--crea-inventory',action='store',default=None)

def pytest_configure(config):
    name=config.getoption('--crea-inventory')
    if not name: raise pytest.UsageError('--crea-inventory is required for this explicit plugin')
    root=Path.cwd().resolve(); raw=Path(name)
    if raw.is_absolute() or '..' in raw.parts: raise pytest.UsageError('inventory must be repository relative')
    target=root/raw
    for p in [target,*target.parents]:
        if p==root: break
        if p.is_symlink() or getattr(p,'is_junction',lambda:False)(): raise pytest.UsageError('inventory links forbidden')
    if target.exists(): raise pytest.UsageError('inventory output already exists')
    # Reserve exclusively before collection; a failing import still leaves evidence.
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x',encoding='utf-8') as stream: stream.write('{}\n')
    config._crea_inventory={'schema_version':'1.0','producer':'crea.pytest_inventory',
        'run_id':hashlib.sha256(os.urandom(32)).hexdigest(),'root':str(root),'exitstatus':-1,'collection_errors':[],'items':[]}
    config._crea_target=target
    config._crea_items={}

def pytest_itemcollected(item):
    data=item.config._crea_inventory
    original=item.nodeid
    path=Path(item.path).resolve().relative_to(Path.cwd().resolve()).as_posix()
    name=path+('::'+original.split('::',1)[1] if '::' in original else '')
    if name in item.config._crea_items: raise pytest.UsageError('duplicate nodeid is ambiguous')
    item._crea_nodeid=name
    row={'nodeid':name,'path':path,'deselected':False,'phases':{}}
    item.config._crea_items[name]=row; data['items'].append(row)
    item.user_properties.extend([('crea.nodeid',name),('crea.run_id',data['run_id'])])

def pytest_deselected(items):
    for item in items: item.config._crea_items[item._crea_nodeid]['deselected']=True

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item,call):
    outcome=yield
    report=outcome.get_result()
    item.config._crea_items[item._crea_nodeid]['phases'][report.when]=report.outcome

def pytest_collectreport(report):
    if report.failed:
        # No traceback, code, parameter values or environment copied.
        _ERRORS.append(report.nodeid)

_ERRORS=[]

def pytest_sessionfinish(session,exitstatus):
    config=session.config
    data=config._crea_inventory; data['exitstatus']=int(exitstatus)
    data['collection_errors']=sorted(set(_ERRORS)); data['items'].sort(key=lambda r:r['nodeid'])
    config._crea_target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
