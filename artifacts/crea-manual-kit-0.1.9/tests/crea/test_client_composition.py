"""Composición controla copia, no reemplaza ignore, contexto o autorización Git."""
import json
import unittest

import test_testing_adapters as legacy
from testing.common import KIT, read

try:
    import composicion
except ImportError:
    composicion=None


class ClientCompositionTests(unittest.TestCase):
    setUp=legacy.AdaptersTests.setUp
    cleanup=legacy.AdaptersTests.cleanup
    write=legacy.AdaptersTests.write
    git=legacy.AdaptersTests.git
    init_git=legacy.AdaptersTests.init_git

    def fixture(self):
        self.assertIsNotNone(composicion,'Composition helper is missing')
        self.write('kit-composition.json',json.dumps({'schema_version':'1.0',
            'client_required':['AGENTS.md','docs/**','kit-composition.json'],
            'distribution_only':['Prompt_configurar-kit-proyecto.txt','LEEME-CREA.md'],
            'local_only':['.crea/local.json','.crea/diagnosticos/**','.git/**'],
            'reasons':{'client_required':'operate','distribution_only':'maintainer','local_only':'personal'}}))
        self.write('AGENTS.md','entry to C\n');self.write('docs/preparar-desarrollador.md','guide\n')
        self.write('Prompt_configurar-kit-proyecto.txt','A/B/C\n');self.write('LEEME-CREA.md','distribution\n')

    def test_client_has_local_entry_without_distribution_prompts(self):
        self.fixture();result=composicion.select(self.root)
        self.assertIn('AGENTS.md',result['client_required'])
        self.assertIn('docs/preparar-desarrollador.md',result['client_required'])
        self.assertNotIn('Prompt_configurar-kit-proyecto.txt',result['client_required'])
        self.assertEqual(result['distribution_only'],['LEEME-CREA.md','Prompt_configurar-kit-proyecto.txt'])

    def test_unclassified_and_ambiguous_files_are_rejected(self):
        self.fixture();self.write('unknown.bin','unknown\n')
        with self.assertRaises(ValueError):composicion.select(self.root)
        (self.root/'unknown.bin').unlink()
        data=read(self.root/'kit-composition.json');data['client_required'].append('LEEME-CREA.md')
        self.write('kit-composition.json',json.dumps(data))
        with self.assertRaises(ValueError):composicion.select(self.root)

    def test_local_binding_is_not_selected_or_read(self):
        self.fixture();self.write('.crea/local.json','not JSON; never load personal values\n')
        result=composicion.select(self.root)
        self.assertNotIn('.crea/local.json',result['client_required'])
        self.assertIn('.crea/local.json',result['local_only'])


if __name__=='__main__':unittest.main()
