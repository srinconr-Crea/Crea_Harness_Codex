"""Candidato de equipo: historia inmutable y cliente sin prompt de distribución."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'scripts/package_manual_019.py'


def module():
    assert PACK.is_file(),'New candidate packager is missing'
    spec=importlib.util.spec_from_file_location('package019',PACK)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def test_packager_only_accepts_new_candidate():
    import pytest
    p=module()
    for version in ('0.1.3','0.1.4','0.1.5','0.1.6','0.1.7','0.1.8'):
        with pytest.raises(ValueError):p.assert_target(ROOT/('artifacts/crea-manual-kit-'+version))
    p.assert_target(p.KIT)


def test_baseline_preserves_historical_artifacts_and_detects_change(scratch):
    import pytest
    p=module()
    original=p.read(ROOT/'docs/hu/habilitar-trabajo-multidesarrollador-kit/baseline.json')
    assert p.verify_baseline(ROOT,original)['source_preserved'] is True
    target=scratch/'source.txt';target.write_text('original')
    baseline={'files':[{'path':'source.txt','bytes':8,'sha256':p.file_hash(target)}]}
    target.write_text('modified')
    with pytest.raises(ValueError):p.verify_baseline(scratch,baseline)


def test_client_selection_operates_without_long_prompt_or_leeme(scratch):
    p=module();target=scratch/'client';target.mkdir()
    selected=p.composition(p.KIT)
    assert 'Prompt_configurar-kit-proyecto.txt' not in selected['client_required']
    assert 'LEEME-CREA.md' not in selected['client_required']
    for name in selected['client_required']:
        source=p.KIT/name;out=target/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(source.read_bytes())
    assert (target/'.agents/skills/Crea/preparar-desarrollador/SKILL.md').is_file()
    assert (target/'tests/crea/test_kit_validation.py').is_file()
    result=subprocess.run([sys.executable,'-B',str(target/'scripts/crea/validar-kit.py'),'--root',str(target)],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    data=json.loads(result.stdout)
    assert data['status']=='passed'
    assert data['business_tests_executed'] is False
