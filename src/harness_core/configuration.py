import hashlib
import json
import os
import re
import stat
from pathlib import Path
from urllib.parse import urlsplit

import yaml
from pydantic import ValidationError

from .contracts import Descriptor, Policy, Binding

LIMIT = 128 * 1024


class ConfigError(ValueError):
    def __init__(self, code, document=None, fields=None):
        self.code = code
        self.document = document
        self.fields = fields or []
        super().__init__(code)


def safe_path(path):
    p = Path(path)
    if ".." in p.parts:
        raise ConfigError("path_traversal")
    p = Path(os.path.abspath(p))
    for part in [*reversed(p.parents), p]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            raise ConfigError("path_unreadable") from None
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ConfigError("linked_path")
    return p


def read_bytes(path):
    p = safe_path(path)
    try:
        if not p.is_file():
            raise ConfigError("not_regular_file")
        with p.open("rb") as stream:
            data = stream.read(LIMIT + 1)
    except OSError:
        raise ConfigError("file_unreadable") from None
    if len(data) > LIMIT:
        raise ConfigError("document_too_large")
    return data


def digest(path):
    return hashlib.sha256(read_bytes(path)).hexdigest()


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ConfigError("duplicate_key")
        result[key] = value
    return result


class UniqueLoader(yaml.SafeLoader):
    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise ConfigError('yaml_alias_not_allowed')
        return super().compose_node(parent, index)


def mapping(loader, node):
    return pairs([(loader.construct_object(k), loader.construct_object(v)) for k, v in node.value])


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def reject_secrets(value, visited=None):
    visited = set() if visited is None else visited
    if isinstance(value, (dict, list)):
        if id(value) in visited:
            raise ConfigError("recursive_document")
        visited.add(id(value))
        for key, item in value.items() if isinstance(value, dict) else enumerate(value):
            if isinstance(key, str) and re.search(r"(^|_)(password|secret|token|credential|api_key|private_key)(_|$)", key, re.I):
                raise ConfigError("secret_not_allowed")
            reject_secrets(item, visited)
        visited.remove(id(value))
    elif isinstance(value, str) and re.search(r"gh[pousr]_[A-Za-z0-9]{20,}|dapi[a-f0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY", value):
        raise ConfigError("secret_not_allowed")


def load_document(path, model=None):
    data = read_bytes(path)
    try:
        text = data.decode("utf-8-sig")
        value = json.loads(text, object_pairs_hook=pairs) if text.lstrip().startswith(("{", "[")) else yaml.load(text, Loader=UniqueLoader)
        if not isinstance(value, dict):
            raise ConfigError("object_required")
        reject_secrets(value)
        return model.model_validate(value) if model else value
    except ConfigError:
        raise
    except ValidationError as error:
        known=set(model.model_fields)
        fields=[]
        for entry in error.errors(include_input=False,include_context=False):
            key=str(entry['loc'][0]) if entry['loc'] else ''
            try:
                reject_secrets(key)
                safe=key in known or bool(re.fullmatch(r'[a-z][a-z_]{0,63}',key))
            except ConfigError:
                safe=False
            fields.append(key if safe else 'unknown_field')
        fields=sorted(set(fields))
        raise ConfigError('invalid_document',model.__name__,fields) from None
    except (ValueError, TypeError, yaml.YAMLError, RecursionError):
        raise ConfigError("invalid_document") from None


def normalize_remote(origin):
    if not origin:
        raise ConfigError("origin_missing")
    if origin.startswith("git@github.com:"):
        name = origin[len("git@github.com:"):]
    else:
        try:
            u = urlsplit(origin)
            if u.hostname != "github.com" or u.query or u.fragment or u.port is not None:
                raise ValueError()
            if not ((u.scheme == "https" and u.username is None) or (u.scheme == "ssh" and u.username == "git" and u.password is None)):
                raise ValueError()
            name = u.path.removeprefix("/")
        except ValueError:
            raise ConfigError("invalid_remote") from None
    name = name.removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", name):
        raise ConfigError("invalid_remote")
    return name.lower()


def validate_configuration(target, policy_path, binding_path, origin, descriptor=None, proposed_binding=None):
    target = safe_path(target)
    policy = load_document(policy_path, Policy)
    binding = proposed_binding or load_document(binding_path, Binding)
    descriptor = descriptor or load_document(target / ".harness/client.yaml", Descriptor)
    if len({descriptor.client_id, policy.client_id, binding.client_id}) != 1:
        raise ConfigError("client_mismatch")
    if descriptor.repository.lower() != policy.repository.lower() or normalize_remote(origin) != policy.repository.lower():
        raise ConfigError("repository_mismatch")
    if descriptor.base_branch != policy.base_branch:
        raise ConfigError("base_branch_mismatch")
    if digest(policy_path) != binding.policy_sha256:
        raise ConfigError("policy_hash_mismatch")
    if not Path(binding.target_path).is_absolute() or safe_path(binding.target_path) != target:
        raise ConfigError("target_mismatch")
    state = Path(binding.state_dir)
    if not state.is_absolute():
        raise ConfigError("state_path_invalid")
    state = safe_path(state)
    if state.is_relative_to(target) or tuple(state.parts[-2:]) != (binding.client_id, binding.checkout_id):
        raise ConfigError("state_path_invalid")
    safe_path(target / descriptor.openspec_root)
    return dict(descriptor=descriptor, policy=policy, binding=binding)
