"""Smoke del wheel instalado en .smoke-venv, aislado de src y del venv dev."""
import hashlib
import json
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[1]
interpreter=root/'.smoke-venv/Scripts/python.exe'
entry=root/'.smoke-venv/Scripts/harness.exe'
results=[]

def check(args,expected):
    run=subprocess.run([str(x) for x in args],cwd=root,capture_output=True,encoding='utf-8',timeout=30)
    assert run.returncode==expected,(args,run.returncode)
    results.append({'command':[str(x.relative_to(root)) if isinstance(x,Path) and x.is_relative_to(root) else str(x) for x in args],
                    'exit_code':run.returncode})
    return run.stdout

assert check([entry,'--version'],0).strip()=='0.1.0'
assert 'doctor' in check([interpreter,'-I','-m','harness_local','--help'],0)
doctor=json.loads(check([entry,'doctor','--path',root,'--json'],0))
assert doctor['status']=='partial'
assert all(c['status']=='ready' for c in doctor['checks'] if c['id'] in ('python','git','node','openspec','databricks'))
assert json.loads(check([entry,'init','--json'],2))['checks'][0]['code']=='apply_not_supported'
assert json.loads(check([entry,'doctor','--policy','absent','--json'],2))['status']=='invalid'
resource_check="from importlib.resources import files; import harness_local; assert 'site-packages' in harness_local.__file__; assert files('harness_local').joinpath('compatibility.json').is_file(); assert files('harness_local').joinpath('templates/AGENTS.md').is_file(); print('installed resources OK')"
assert 'OK' in check([interpreter,'-I','-c',resource_check],0)
wheel=root/'dist/crea_local_harness-0.1.0-py3-none-any.whl'
from zipfile import ZipFile
with ZipFile(wheel) as archive:
    names=archive.namelist()
    assert {name for name in names if '/fixtures/' in name} == {
        'harness_local/quality_kit/fixtures/synthetic-sales.json'}
    assert not any('client.yaml' in name for name in names)
result={'schema_version':1,'wheel':wheel.name,'sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),
        'checks':results,'doctor':doctor,'wheel_files':names}
destination=root/'docs/evidence/wheel-smoke.json'
destination.parent.mkdir(parents=True,exist_ok=True)
destination.write_text(json.dumps(result,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print(f'{len(results)} smoke checks passed; wheel resources and isolation verified')
