import json
import subprocess

from test_validation import plan,request,api
from test_validation_remote import target,ServiceDouble
from harness_core.onboarding_plan import sha


def test_bundle_profile_host_target_checked_before_call(scratch):
    from harness_local.validation_bundle import run_bundle
    p=plan('yaml-dabs',impacts=['integration']); r=request(p,'bundle-validate')
    s=ServiceDouble(); s.bundle_validate=lambda *args: (_ for _ in ()).throw(AssertionError('unexpected execution'))
    raw=b'bundle:\n  name: synthetic\nworkspace:\n  host: https://prod.example.invalid\n'
    e=run_bundle(p,r,target(),raw,state_dir=scratch,provider=s)
    assert e.status=='blocked' and e.reason=='bundle_target_mismatch'
    assert s.calls==[]


def test_bundle_rejects_scripts_includes_and_global_paths(scratch):
    from harness_local.validation_bundle import run_bundle
    p=plan('yaml-dabs',impacts=['integration']); r=request(p,'bundle-validate')
    for suffix in ('include: [private.yml]\n','scripts:\n  x: echo private\n','sync:\n  paths: [/private]\n'):
        raw=('bundle:\n  name: synthetic\nworkspace:\n  host: https://sandbox.example.invalid\n'+suffix).encode()
        assert run_bundle(p,r,target(),raw,state_dir=scratch,provider=ServiceDouble()).status=='blocked'


def test_bundle_authorized_read_only_cli_result(scratch):
    from harness_local.validation_bundle import run_bundle
    p=plan('yaml-dabs',impacts=['integration']); raw=b'bundle:\n  name: synthetic\nworkspace:\n  host: https://sandbox.example.invalid\n'
    r=request(p,'bundle-validate',source_sha256=sha(raw)); s=ServiceDouble()
    s.bundle_validate=lambda t,path: dict(workspace={'host':t.host},bundle={'name':'synthetic'})
    e=run_bundle(p,r,target(),raw,state_dir=scratch,provider=s)
    assert e.status=='passed' and e.scope=='authorized-bundle' and e.simulated
    assert e.remote_run_id is None and not list(scratch.glob('bundle-*'))
