import hashlib
import json
from pathlib import Path
import subprocess
import uuid

import pytest


@pytest.fixture
def scratch():
    # Windows sandbox: default ACL inheritance, avoiding tempfile's owner-only ACL.
    p=Path(".test-data")/uuid.uuid4().hex
    p.mkdir(parents=True)
    return p.resolve()


@pytest.fixture
def client(scratch):
    target=scratch/"target"
    target.mkdir()
    subprocess.run(["git","init","--initial-branch=develop",str(target)],check=True,capture_output=True)
    origin="https://github.com/demo/alpha.git"
    subprocess.run(["git","-C",str(target),"remote","add","origin",origin],check=True,capture_output=True)
    (target/".harness").mkdir()
    descriptor=dict(schema_version=1,client_id="alpha",repository="demo/alpha",base_branch="develop",openspec_root="openspec")
    (target/".harness/client.yaml").write_text(json.dumps(descriptor))
    policy=scratch/"policy.json"
    policy.write_text(json.dumps(dict(schema_version=1,policy_id="pilot",client_id="alpha",
        repository="demo/alpha",base_branch="develop",branch_prefix="feature/",
        read_only_paths=[".harness/"],denied_paths=["private/"],max_files=40,max_bytes=2000000)))
    binding=scratch/"binding.json"
    binding.write_text(json.dumps(dict(schema_version=1,client_id="alpha",checkout_id="checkout",
        target_path=str(target),policy_sha256=hashlib.sha256(policy.read_bytes()).hexdigest(),
        state_dir=str(scratch/"state/alpha/checkout"))))
    return dict(target=target,policy=policy,binding=binding,origin=origin)
