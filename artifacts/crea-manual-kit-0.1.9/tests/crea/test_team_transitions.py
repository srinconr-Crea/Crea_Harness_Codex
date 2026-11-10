"""El destino canónico y la compatibilidad se consumen sin efectos remotos."""
import json
import unittest

import test_testing_adapters as legacy
import test_transiciones as transition_fixtures
import test_target_compatibility as compatibility_fixtures
from testing.common import KIT, read, write, file_hash
import transiciones
import compatibilidad


class TeamTransitionTests(unittest.TestCase):
    setUp=legacy.AdaptersTests.setUp
    cleanup=legacy.AdaptersTests.cleanup
    write=legacy.AdaptersTests.write
    git=legacy.AdaptersTests.git
    init_git=legacy.AdaptersTests.init_git
    setup_handoff=transition_fixtures.TransitionTests.setup_handoff
    graph=compatibility_fixtures.TargetCompatibilityTests.graph
    review=compatibility_fixtures.TargetCompatibilityTests.review
    simulation=compatibility_fixtures.TargetCompatibilityTests.simulation

    def test_changed_target_does_not_reuse_old_delivery_authorization(self):
        h,name=self.setup_handoff();p=read(self.root/'docs/proyecto.json')
        p['delivery']['pr_target_branch']='quality';write(self.root/'docs/proyecto.json',p)
        h['evidence']['delivery']={'title':'approved title','body':'approved body','repository':'https://github.com/example/repo',
            'source_branch':'feature/HU001','target_branch':'main','head_sha':self.git('rev-parse','HEAD'),'status':'draft'}
        write(self.root/name,h)
        result=transiciones.check(self.root,name,'to_apply')
        self.assertIn('DELIVERY_TARGET_MISMATCH',result['existing_constraints'])

    def test_stale_compatibility_is_advisory_until_explicit_promotion(self):
        self.assertTrue(hasattr(transiciones,'check_compatibility'),'Compatibility consumer is missing')
        p,h,s=self.graph();sim=self.simulation(h,s)
        first=compatibilidad.inspect(self.root,p,h,s,simulation=sim)
        report=compatibilidad.inspect(self.root,p,h,s,simulation=sim,semantic_review=self.review(first))
        report['freshness']='stale'
        name='docs/hu/HU002/compatibilidad/attempt-1/report.json';self.write(name,json.dumps(report))
        h['evidence']['compatibility']={'path':name,'sha256':file_hash(self.root/name)}
        observed=transiciones.check_compatibility(self.root,p,h)
        self.assertIn('TARGET_COMPATIBILITY_CURRENT',[x['condition_id'] for x in observed['findings']])
        self.assertEqual(observed['existing_constraints'],[])
        self.assertEqual(observed['findings'][0]['class'],'blocking_noncompliance')
        # The existing consumer decides effect using mode and promotion, not the classification alone.
        decision=transiciones.consume({'check_status':'completed','new_control_effect':'report_only','findings':observed['findings']},0,'informative',[])
        self.assertTrue(decision['can_continue'])


if __name__=='__main__':unittest.main()
