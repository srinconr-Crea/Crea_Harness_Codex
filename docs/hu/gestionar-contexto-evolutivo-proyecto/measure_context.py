"""Recibo local reproducible: mide únicamente inspección de contexto sintético."""
from pathlib import Path
import json
import subprocess
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
KIT=ROOT/'artifacts/crea-manual-kit-0.1.7'
sys.path.insert(0,str(KIT/'tests/crea'))
from test_contexto import ContextTests,contexto,document

fixture=ContextTests(); fixture.setUp()
try:
    fixture.setup_context()
    for index in range(200): fixture.write(f'unrelated/docs/{index:03}.md','Contenido ajeno\n'*256)
    fixture.write('.env','SYNTHETIC_CREDENTIAL_NOT_TO_LOAD')
    calls=[]; reads=[]; original_run=subprocess.run; original_open=Path.open
    def git_only(argv,*args,**kw):
        assert argv[0]=='git' and not set(argv)&{'push','pull','fetch','clone','ls-remote'}
        calls.append(argv)
        return original_run(argv,*args,**kw)
    def selected_only(path,*args,**kw):
        reads.append(path.relative_to(fixture.root).as_posix())
        return original_open(path,*args,**kw)
    with patch.object(subprocess,'run',git_only),patch.object(Path,'open',selected_only):
        result=fixture.inspect()
    assert set(reads)=={'docs/app.md','docs/shared.md'}
    assert '.env' in result['observation']['paths']
    assert len(calls)==result['metrics']['git_processes']
    receipt={'kind':'synthetic_context_inspection_receipt','source_version':'0.1.6','candidate_version':'0.1.7',
        'metrics':result['metrics'],'actual_process_executables':[argv[0] for argv in calls],
        'actual_context_read_paths':reads,'unrelated_documents':200,'unrelated_bytes':200*len(('Contenido ajeno\n'*256).encode()),
        'changed_secret_detected_by_git':'.env' in result['observation']['paths'],
        'changed_paths_observed':len(result['observation']['paths']),
        'sources':result['semantic']['sources'],'impact':result['semantic']['impact'],
        'suite_processes_observed':0,'remote_processes_observed':0,
        'runtime_required_inactive':'blocked (covered by test_silver_required_inactive_runtime_stays_blocked_without_process)',
        'native_agents':'not_run','remote_pilot':'not_run','universal_time_claim':False}
    target=ROOT/'docs/hu/gestionar-contexto-evolutivo-proyecto/inspection-metrics.json'
    target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))
finally:
    fixture.doCleanups()
