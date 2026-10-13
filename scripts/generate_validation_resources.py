"""Package only reviewed passive validation templates and their byte manifest."""
import json
from pathlib import Path
from harness_core.onboarding_plan import sha

root=Path(__file__).resolve().parents[1]
source=root/'resources/validation'; target=root/'src/harness_local/validation_kit'
target.mkdir(parents=True,exist_ok=True)
entries=[]
for path in sorted(source.glob('*.py')):
    raw=path.read_bytes(); (target/path.name).write_bytes(raw)
    entries.append(dict(path=path.name,sha256=sha(raw),bytes=len(raw)))
(target/'manifest.json').write_text(json.dumps(dict(schema_version=1,files=entries),indent=2)+'\n',encoding='utf-8')
