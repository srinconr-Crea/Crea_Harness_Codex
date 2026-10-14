from pathlib import Path
import json
import subprocess

LAUNCHER=Path('src/harness_local/distribution_kit/launcher.ps1').resolve()


def invoke(*args):
    # Process-only policy for this reviewed local fixture; never changes user/machine policy.
    return subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','RemoteSigned','-File',str(LAUNCHER),*map(str,args)],capture_output=True,text=True,timeout=30)


def test_launcher_clean_machine_preview_is_read_only(scratch):
    before=list(scratch.iterdir())
    run=invoke()
    assert run.returncode==0
    result=json.loads(run.stdout)
    assert result['status']=='partial' and result['trust']=='pending' and not result['certified']
    assert list(scratch.iterdir())==before


def args(project,venv):
    return ('-Apply','-ProjectRoot',project,'-Venv',venv,'-Wheelhouse',project,
        '-Wheel',project/'missing.whl','-Lock',project/'missing.txt','-WheelSha256','a'*64)


def test_launcher_rejects_outside_project_before_install(scratch):
    project=scratch/'project';project.mkdir();(project/'.git').mkdir()
    venv=scratch/'outside'
    run=invoke(*args(project,venv))
    assert run.returncode!=0 and 'within the selected project' in run.stderr
    assert not venv.exists()


def test_launcher_rejects_junction_parent(scratch):
    project=scratch/'project';project.mkdir();(project/'.git').mkdir()
    outside=scratch/'outside';outside.mkdir()
    link=project/'junction'
    subprocess.run(['cmd.exe','/c','mklink','/J',str(link),str(outside)],check=True,capture_output=True)
    run=invoke(*args(project,link/'venv'))
    assert run.returncode!=0 and 'Linked path rejected' in run.stderr
    assert not (outside/'venv').exists()
