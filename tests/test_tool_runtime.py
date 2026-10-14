import hashlib
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pytest

from harness_core.setup import InstalledTool
from harness_local.tool_runtime import compatible,discover


@pytest.mark.parametrize('version,accepted',[('0.277.0',False),('0.292.0',True),('1.18.0',True)])
def test_recorded_databricks_obeys_matrix(monkeypatch,version,accepted):
    runtime=Path(sys.executable)
    tool=InstalledTool(schema_version=1,name='databricks',version=version,path=str(runtime),
        sha256=hashlib.sha256(runtime.read_bytes()).hexdigest(),license='synthetic-double')
    record=SimpleNamespace(runtime_path=str(runtime),tools=[tool])
    monkeypatch.setattr(shutil,'which',lambda _:None)
    names={tool.name for tool in discover(record,{'databricks'})}
    assert ('databricks' in names)==accepted
    assert compatible('databricks',version)==accepted
