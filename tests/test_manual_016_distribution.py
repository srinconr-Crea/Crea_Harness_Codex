import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def scratch():
    # Ordinary mkdir preserves inherited Windows ACLs; pytest's private temp ACL
    # cannot be traversed by the managed sandbox on this host.
    path = ROOT / '.test-data' / ('016-distribution-' + uuid.uuid4().hex)
    path.mkdir(parents=True)
    return path


def load_package():
    path = ROOT / 'scripts/package_manual_016.py'
    assert path.is_file(), 'Version-specific 0.1.6 packager is missing'
    spec = importlib.util.spec_from_file_location('package_016', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rejects_historical_targets():
    package = load_package()
    for version in ('0.1.3', '0.1.4', '0.1.5'):
        with pytest.raises(ValueError, match='TARGET'):
            package.assert_target(ROOT / 'artifacts' / ('crea-manual-kit-' + version))
    package.assert_target(ROOT / 'artifacts/crea-manual-kit-0.1.6')


def test_detects_baseline_change_without_trusting_historical_manifest(scratch):
    tmp_path = scratch
    package = load_package()
    source = tmp_path / 'artifacts/crea-manual-kit-0.1.5/Prompt_configurar-kit-proyecto.txt'
    source.parent.mkdir(parents=True)
    source.write_bytes(b'user prompt')
    baseline = {'files': [{'path': source.relative_to(tmp_path).as_posix(),
                           'bytes': 11, 'sha256': hashlib.sha256(b'user prompt').hexdigest()}]}
    assert package.verify_baseline(tmp_path, baseline)['source_preserved'] is True
    source.write_bytes(b'changed')
    with pytest.raises(ValueError, match='BASELINE_CHANGED'):
        package.verify_baseline(tmp_path, baseline)


def test_archive_matches_tree_and_omits_local_state(scratch):
    tmp_path = scratch
    package = load_package()
    kit = tmp_path / 'kit'
    kit.mkdir()
    (kit / 'Prompt_configurar-kit-proyecto.txt').write_text('prompt', encoding='utf-8')
    (kit / '.agents').mkdir()
    (kit / '.agents/SKILL.md').write_text('skill', encoding='utf-8')
    (kit / '__pycache__').mkdir()
    (kit / '__pycache__/noise.pyc').write_bytes(b'noise')
    target = tmp_path / 'kit.zip'
    report = package.write_archive(kit, target)
    with zipfile.ZipFile(target) as archive:
        assert set(archive.namelist()) == {'kit/Prompt_configurar-kit-proyecto.txt', 'kit/.agents/SKILL.md'}
    assert report['zip_entries'] == 2
    assert report['zip_sha256'] == hashlib.sha256(target.read_bytes()).hexdigest()


def test_manifest_contains_prompt_and_preserves_source_baseline():
    package = load_package()
    baseline = json.loads((ROOT / 'docs/evidence/portable-aitools-devops/baseline.json').read_text(encoding='utf-8'))
    assert any(row['path'].endswith('0.1.5/Prompt_configurar-kit-proyecto.txt') for row in baseline['files'])
    assert package.verify_baseline(ROOT, baseline)['source_preserved'] is True
