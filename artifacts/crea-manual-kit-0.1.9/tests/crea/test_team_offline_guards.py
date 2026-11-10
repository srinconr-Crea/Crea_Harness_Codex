"""Read-only guards observed at both Git process boundaries."""
import subprocess
import unittest
from unittest.mock import patch
import test_testing_adapters as legacy
import entrega
import team_common
from testing import git_adapter, schemas
from testing.common import KIT, read


class OfflineGuardsTests(unittest.TestCase):
    def test_positional_repository_identity_allows_equal_segments(self):
        import test_target_compatibility as fixtures
        fixture=fixtures.TargetCompatibilityTests()
        fixture.setUp()
        try:
            _,_,snapshot=fixture.graph()
            snapshot['repository']=['azure','org','pets','pets']
            schemas.validate_schema(read(KIT/'docs/plantillas/git-target-snapshot.schema.json'),snapshot)
        finally:fixture.doCleanups()

    def test_git_observers_disable_fsmonitor_and_implicit_lazy_fetch(self):
        response=subprocess.CompletedProcess([],0,b'ok',b'')
        with patch('subprocess.run',return_value=response) as launched:
            git_adapter.git(KIT,'status','--porcelain')
            args,kwargs=launched.call_args
            self.assertIn('core.fsmonitor=false',args[0])
            self.assertEqual(kwargs['env']['GIT_NO_LAZY_FETCH'],'1')
            self.assertEqual(kwargs['env']['GIT_OPTIONAL_LOCKS'],'0')
        with patch('subprocess.run',return_value=response) as launched:
            team_common.git_result(KIT,'cat-file','-e','HEAD')
            self.assertEqual(launched.call_args.kwargs['env']['GIT_NO_LAZY_FETCH'],'1')
            self.assertEqual(launched.call_args.kwargs['env']['GIT_OPTIONAL_LOCKS'],'0')

    def test_remote_statuses_are_not_branch_creation_authority(self):
        for code,stderr,expected in [(2,b'','missing'),(128,b'authentication failed','access_denied'),
                                     (128,b'network unreachable','connection_error')]:
            with self.subTest(expected=expected),patch.object(entrega,'git_result',return_value=subprocess.CompletedProcess([],code,b'',stderr)):
                self.assertEqual(entrega.remote_sha(KIT,'origin','quality'),(None,expected))

    def test_render_includes_canonical_compatibility_refs_and_hashes(self):
        from test_transiciones import handoff
        from testing.common import render_handoff
        value=handoff()
        value['evidence']['compatibility']={'path':'docs/hu/synthetic/compatibilidad/attempt-1/report.json','sha256':'a'*64}
        value['evidence']['target_snapshot']={'path':'docs/hu/synthetic/compatibilidad/attempt-1/target.json','sha256':'b'*64}
        output=render_handoff(value,'handoff.json','c'*64)
        for ref in [value['evidence']['compatibility'],value['evidence']['target_snapshot']]:
            self.assertIn(ref['path'],output);self.assertIn(ref['sha256'],output)


if __name__=='__main__':unittest.main()
