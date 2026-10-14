"""Scoped product IO uses pinned Windows handles; no Desktop interception."""
from harness_core.configuration import ConfigError
from harness_core.setup import authorize_access
from .windows_fs import PinnedTree


class ScopedTree:
    def __init__(self, target, scope, policy, plan_paths):
        self.target, self.scope, self.policy, self.plan_paths=target,scope,policy,list(plan_paths)
        self.tree=None

    def __enter__(self):
        self.tree=PinnedTree(self.target)
        return self

    def __exit__(self,*args):
        if self.tree: self.tree.__exit__(*args)

    def read(self,path,limit=128*1024):
        authorize_access(self.scope,self.policy,path,'read',self.plan_paths)
        with self.tree.file(path) as handle:
            if str(handle.final_path())!=str(self.tree.root / path): raise ConfigError('destination_alias')
            return handle.read(limit)

    def create(self,path,data):
        authorize_access(self.scope,self.policy,path,'write',self.plan_paths)
        if len(data)>self.policy.max_bytes: raise ConfigError('access_denied')
        self.check_parent(path)
        with self.tree.file(path,create=True) as handle: handle.write(data)

    def check_parent(self,path):
        from pathlib import PurePosixPath
        parent=PurePosixPath(path).parent.as_posix()
        if parent!='.':
            with self.tree.directory(parent) as handle:
                if str(handle.final_path())!=str(self.tree.root / parent): raise ConfigError('destination_alias')

    def replace(self,path,data,expected_sha256):
        """Requires read access, explicit expected contents and a caller journal."""
        from harness_core.onboarding_plan import sha
        authorize_access(self.scope,self.policy,path,'write',self.plan_paths,read_required=True)
        if len(data)>self.policy.max_bytes: raise ConfigError('access_denied')
        with self.tree.editable_file(path) as handle:
            if str(handle.final_path())!=str(self.tree.root / path): raise ConfigError('destination_alias')
            if sha(handle.read())!=expected_sha256: raise ConfigError('plan_stale')
            handle.replace_bytes(data)
