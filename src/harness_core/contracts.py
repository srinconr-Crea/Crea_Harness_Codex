import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, AfterValidator, BeforeValidator


def identifier(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise ValueError("invalid identifier")
    return value


def repository(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", value):
        raise ValueError("invalid repository")
    if any(x in (".", "..") or x.endswith(".git") for x in value.split("/")):
        raise ValueError("invalid repository")
    return value


def branch(value):
    if (not value or value == "@" or value.startswith(("/", "-")) or value.endswith(("/", "."))
        or any(x in value for x in ("..", "@{", "//"))
        or re.search(r"[\x00-\x20\x7f~^:?*\[\\]", value)
        or any(x.startswith(".") or x.endswith(".lock") for x in value.split("/"))):
        raise ValueError("invalid branch")
    return value


def relative(value):
    clean = value[:-1] if value.endswith('/') else value
    if (not clean or "\\" in value or ":" in value or value.startswith("/")
        or any(x in ("", ".", "..") for x in clean.split("/"))
        or any(ord(x) < 32 for x in value)):
        raise ValueError("invalid relative path")
    return value


ID = Annotated[str, Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$'), AfterValidator(identifier)]
Repo = Annotated[str, Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$'), AfterValidator(repository)]
Branch = Annotated[str, AfterValidator(branch)]
Relative = Annotated[str, AfterValidator(relative)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Annotated[Literal[1], BeforeValidator(lambda v: v if type(v) is int else (_ for _ in ()).throw(ValueError('integer version required')))]


class Descriptor(Contract):
    client_id: ID
    repository: Repo
    base_branch: Branch
    openspec_root: Relative = "openspec"


class Policy(Contract):
    policy_id: ID
    client_id: ID
    repository: Repo
    base_branch: Branch
    branch_prefix: Annotated[str, AfterValidator(lambda v: branch(v[:-1]) + "/" if v.endswith("/") else branch(v))]
    read_only_paths: list[Relative]
    denied_paths: list[Relative]
    max_files: Annotated[int, Field(gt=0)]
    max_bytes: Annotated[int, Field(gt=0)]


class Binding(Contract):
    client_id: ID
    checkout_id: ID
    target_path: str
    policy_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    state_dir: str
    databricks_profile: ID | None = None
