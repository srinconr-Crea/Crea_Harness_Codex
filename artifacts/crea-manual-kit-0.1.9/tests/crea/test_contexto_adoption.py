"""Adopción revisada de contexto con configuración personalizada."""
import copy
import json
from pathlib import Path
import unittest
import test_testing_adapters as legacy
from testing import kit_validation
from testing.common import KIT,read,file_hash

class AdoptionTests(unittest.TestCase):
    setUp=legacy.AdaptersTests.setUp
    cleanup=legacy.AdaptersTests.cleanup
    write=legacy.AdaptersTests.write

    def test_enabled_customization_preserves_models_and_manual_project_content(self):
        config=read(KIT/'docs/proyecto.json'); config['context_management']['enabled']=True
        config['project']['name']='Cliente personalizado'; config['project']['description']='Decisión manual conservada'
        previous=copy.deepcopy(config)
        profiles={p.name:file_hash(p) for p in (KIT/'.codex/agents').glob('*.toml')}
        result=kit_validation.validate_kit(KIT,config_override=config)
        self.assertTrue(result['context_management_enabled'])
        self.assertEqual(config,previous)
        self.assertEqual(profiles,{p.name:file_hash(p) for p in (KIT/'.codex/agents').glob('*.toml')})

    def test_enabled_adoption_rejects_missing_helper_and_old_contract_schema(self):
        config=read(KIT/'docs/proyecto.json'); config['context_management']['enabled']=True
        self.write('docs/proyecto.schema.json',(KIT/'docs/proyecto.schema.json').read_text(encoding='utf-8'))
        with self.assertRaisesRegex(ValueError,'REQUIRED_FILE_MISSING: scripts/crea/contexto.py'):
            kit_validation.validate_kit(self.root,config_override=config)

    def test_profiles_describe_phase_selection_and_assigned_write_scope(self):
        import tomllib
        for role in ['planner','developer','tester','reviewer']:
            profile=tomllib.loads((KIT/f'.codex/agents/{role}.toml').read_text(encoding='utf-8'))
            text=profile['developer_instructions']
            self.assertIn('Contexto opcional 0.1.7',text)
            self.assertIn('read_paths/write_paths',text)
            self.assertIn('scripts/crea/CONTEXTO.md',text)
        text=(KIT/'docs/contexto-proyecto.md').read_text(encoding='utf-8')
        self.assertIn('developer → tester → reviewer',text)
        self.assertEqual(text.count('## 10.'),1)

if __name__=='__main__': unittest.main()
