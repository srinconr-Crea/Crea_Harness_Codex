"""Integrity-checked package resources; loading never executes upstream code."""
import hashlib
import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from harness_core.configuration import ConfigError, pairs, safe_path
from harness_core.contracts import relative
from harness_core.quality import (
    DOCUMENT_LIMIT, PracticePack, TestCatalog, EvalCatalog, decode_definition,
    validate_catalogs,
)

UPSTREAM_COMMIT = 'ba45d10df7413de14c32937bbd584aeee17d22a2'
UPSTREAM_SOURCE = 'https://github.com/databricks/databricks-agent-skills'
SKILLS = {'databricks-core', 'databricks-dabs', 'databricks-dbsql', 'databricks-jobs',
          'databricks-python-sdk', 'databricks-pipelines', 'databricks-synthetic-data-gen',
          'databricks-mlflow-evaluation', 'databricks-docs'}


@dataclass(frozen=True)
class QualityBundle:
    practices: PracticePack
    tests: TestCatalog
    evals: EvalCatalog
    fixture_bytes: bytes
    dataset_sha256: str
    manifest_sha256: str
    upstream_commit: str
    upstream_license: str


def read(root, path):
    relative(path)
    target = root.joinpath(path)
    if isinstance(target, Path):
        target = safe_path(target)
    with target.open('rb') as stream:
        data = stream.read(DOCUMENT_LIMIT + 1)
    if len(data) > DOCUMENT_LIMIT:
        raise ConfigError('document_too_large')
    return data


def checked_files(root, entries):
    if not isinstance(entries, list) or not 1 <= len(entries) <= 256:
        raise ValueError('invalid_manifest')
    result = {}
    for entry in entries:
        if set(entry) - {'path', 'sha256', 'bytes', 'url'}:
            raise ValueError('invalid_manifest')
        path = entry['path']
        if path in result or type(entry['bytes']) is not int:
            raise ValueError('invalid_manifest')
        content = read(root, path)
        if len(content) != entry['bytes'] or hashlib.sha256(content).hexdigest() != entry['sha256']:
            raise ValueError('resource_integrity')
        result[path] = content
    return result


def load_quality(root=None):
    root = root if root is not None else files('harness_local').joinpath('quality_kit')
    try:
        raw = read(root, 'manifest.json')
        manifest = json.loads(raw, object_pairs_hook=pairs)
        if type(manifest['schema_version']) is not int or manifest['schema_version'] != 1:
            raise ValueError('invalid_manifest')
        contents = checked_files(root, manifest['files'])
        vendor_prefix = 'vendor/databricks-agent-skills/'
        source = json.loads(contents[vendor_prefix + 'SOURCE.json'], object_pairs_hook=pairs)
        if (source['commit'] != UPSTREAM_COMMIT or source['source'] != UPSTREAM_SOURCE
            or source['license'] != 'Databricks License' or set(source['skills']) != SKILLS):
            raise ValueError('invalid_upstream_lock')
        vendor = checked_files(root.joinpath(vendor_prefix), source['files'])
        required = {'LICENSE', 'NOTICE', 'manifest.json', 'README.md',
                    *[f'skills/{skill}/SKILL.md' for skill in SKILLS]}
        if not required <= set(vendor):
            raise ValueError('missing_upstream_resources')
        if set(contents) != {'practices.json', 'test-cases.json', 'eval-cases.json',
                             'fixtures/synthetic-sales.json', vendor_prefix + 'SOURCE.json',
                             *[vendor_prefix + name for name in vendor]}:
            raise ValueError('invalid_resource_set')
        for entry in source['files']:
            if entry['url'] != f'https://raw.githubusercontent.com/databricks/databricks-agent-skills/{UPSTREAM_COMMIT}/{entry["path"]}':
                raise ValueError('invalid_upstream_url')
        p = decode_definition(contents['practices.json'], PracticePack)
        t = decode_definition(contents['test-cases.json'], TestCatalog)
        e = decode_definition(contents['eval-cases.json'], EvalCatalog)
        p, t, e = validate_catalogs(p.model_dump(), t.model_dump(), e.model_dump())
        fixture = contents[t.fixture_ref]
        # Decode only data; no imports, subprocess, network or activation.
        json.loads(fixture, object_pairs_hook=pairs)
        return QualityBundle(p, t, e, fixture, hashlib.sha256(fixture).hexdigest(),
                             hashlib.sha256(raw).hexdigest(), source['commit'], source['license'])
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        raise ConfigError('quality_resources_invalid') from None
