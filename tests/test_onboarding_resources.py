import shutil
from importlib.resources import files

import pytest

from harness_core.configuration import ConfigError


def test_kit_resource_integrity_and_missing(scratch):
    from harness_local.resources import kit
    resources, manifest = kit()
    assert len(resources) == 8
    assert resources['openspec/config.yaml'].startswith('schema: spec-driven')
    assert len(manifest) == 64
    root = scratch / 'resources'
    shutil.copytree(str(files('harness_local').joinpath('openspec_kit')), root)
    skill = root / '.agents/skills/openspec-apply-change/SKILL.md'
    skill.write_text('modified')
    with pytest.raises(ConfigError, match='kit_resources_invalid'):
        kit(root)
    skill.unlink()
    with pytest.raises(ConfigError, match='kit_resources_invalid'):
        kit(root)
