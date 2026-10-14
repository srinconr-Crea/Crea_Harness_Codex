"""Importer mechanics only: all evidence here is synthetic and never exported as acceptance."""
import json
from importlib.resources import files

import pytest

from harness_core.desktop import activate_profiles, DesktopCertificate
from harness_core.distribution import PilotReport, PROTOCOLS
from harness_core.onboarding_plan import canonical, sha
from harness_core.evaluation import select_cases
from harness_local.desktop_resources import load_desktop
from harness_local.distribution import candidate_manifest, release_gate
from test_agent_evaluation import profile, capture, bundle


@pytest.fixture
def imported(scratch):
    candidate=candidate_manifest().manifest_sha256
    catalog=load_desktop()
    catalog=activate_profiles(catalog,{r.id:dict(model='luna',effort='medium') for r in catalog.roles},{'luna':['medium']})
    observations=[]
    for role in catalog.roles:
        surfaces={'role','model-effort','permissions','skill:harness-hu'}|{'tool:'+t.id for t in role.tools}
        for surface in surfaces:
            observations.append(dict(schema_version=1,role=role.id,surface=surface,source='desktop',
                status='observed',model='luna',effort='medium',effective_sandbox=role.sandbox,evidence_ref='fixture'))
    certificate=DesktopCertificate(schema_version=1,catalog_sha256=catalog.sha256,app_version='test-app',
        engine_version='test-engine',account_ref='test-account',observations=observations)
    def save(name,value):
        raw=canonical(value)
        (scratch/name).write_bytes(raw)
        return sha(raw)
    receipts=[]
    for protocol in PROTOCOLS:
        value=dict(candidate_sha256=candidate,protocol=protocol,status='passed',source='desktop_harness',simulated=False)
        receipts.append(dict(schema_version=1,protocol=protocol,status='passed',source='desktop_harness',
            evidence_path=protocol+'.json',evidence_sha256=save(protocol+'.json',value)))
    configs={}
    profiles=[]
    for name in ('baseline','candidate'):
        config=dict(candidate_sha256=candidate,engine_version='test-engine',model='luna',effort='medium',
            surface='desktop',runtime='test-app',roles_sha256=catalog.sha256,
            practices_sha256=sha(files('harness_local').joinpath('quality_kit/practices.json').read_bytes()),tools={'harness':'0.1.0'})
        configs[name]=save(name+'.json',config)
        profiles.append(profile(name,config_sha256=sha(canonical(config)),runtime='test-app',
            roles_sha256=config['roles_sha256'],practices_sha256=config['practices_sha256'],configuration_evidence_ref=name))
    cases,_=select_cases(bundle().evals,milestone=7,purpose='promotion')
    # Claimed real flags test input validation; no genuine model execution occurs.
    runs=[capture(c,p,n,simulated=False).model_dump() for p in profiles for c in cases for n in (1,2,3)]
    evaluation=dict(schema_version=1,milestone=7,purpose='promotion',profiles=[p.model_dump() for p in profiles],
        runs=runs,budget_runs=144,execution_mode='manual')
    report=PilotReport(schema_version=1,candidate_sha256=candidate,implementation_status='complete',receipts=receipts,
        evaluation_path='eval.json',evaluation_sha256=save('eval.json',evaluation),
        catalog_path='catalog.json',catalog_sha256=save('catalog.json',catalog.model_dump()),
        certificate_path='certificate.json',certificate_sha256=save('certificate.json',certificate.model_dump()),
        configuration_evidence=configs)
    return scratch,report,evaluation,save


def test_complete_import_gate_mechanics(imported):
    root,pilot,_,_=imported
    result,code=release_gate(pilot,evidence_root=root)
    assert code==0 and result['certified'] and result['release_allowed']
    assert not result['publication_allowed']


@pytest.mark.parametrize('change',['cli','simulated','roles','model','practices','config','not_run'])
def test_complete_import_rejects_invalid_eval_identity(imported,change):
    root,pilot,evaluation,save=imported
    for p in evaluation['profiles']:
        old=sha(canonical(p))
        if change=='cli': p['surface']='cli'
        if change=='roles': p['roles_sha256']='a'*64
        if change=='model': p['model']='other-model'
        if change=='practices': p['practices_sha256']='a'*64
        if change=='config': p['config_sha256']='a'*64
        new=sha(canonical(p))
        for r in evaluation['runs']:
            if r['profile_sha256']==old:
                r['profile_sha256']=new
                if change=='cli': r['surface']='cli'
                if change=='simulated': r['simulated']=True
                if change=='not_run': r['status']='not_run'
    pilot=pilot.model_copy(update={'evaluation_sha256':save('eval.json',evaluation)})
    result,code=release_gate(pilot,evidence_root=root)
    assert code==1 and not result['certified'] and not result['release_allowed']


@pytest.mark.parametrize('change',['missing','drift','manual','candidate'])
def test_complete_import_rejects_bad_protocol(imported,change):
    root,pilot,_,_=imported
    receipt=pilot.receipts[0]
    if change=='missing': (root/receipt.evidence_path).unlink()
    if change=='drift': (root/receipt.evidence_path).write_text('{}')
    if change=='manual': receipt.source='manual_git'
    if change=='candidate': pilot.candidate_sha256='a'*64
    assert release_gate(pilot,evidence_root=root)[1]==1
