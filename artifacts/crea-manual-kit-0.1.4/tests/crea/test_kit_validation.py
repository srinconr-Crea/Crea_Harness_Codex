import copy
import json
from pathlib import Path
import shutil
import sys
import unittest
import uuid

KIT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KIT / 'scripts/crea'))
try:
    from testing.kit_validation import validate_kit
except ImportError:
    validate_kit = None


class KitValidationTests(unittest.TestCase):
    def test_nested_registered_skill_is_valid_and_unknown_required_check_is_rejected(self):
        self.assertIsNotNone(validate_kit, 'Structural validation adapter missing')
        validate_kit(KIT)
        config = json.loads((KIT / 'docs/proyecto.json').read_text())
        config['validation']['required_checks'] = ['unknown-check']
        with self.assertRaises(ValueError):
            validate_kit(KIT, config_override=config)

    def test_duplicate_or_escaping_registered_skill_is_rejected(self):
        self.assertIsNotNone(validate_kit)
        config = json.loads((KIT / 'docs/proyecto.json').read_text())
        config['extensions']['skills'].append(copy.deepcopy(config['extensions']['skills'][-1]))
        with self.assertRaises(ValueError):
            validate_kit(KIT, config_override=config)
        config['extensions']['skills'].pop()
        config['extensions']['skills'][-1]['path'] = '../outside/SKILL.md'
        with self.assertRaises(ValueError):
            validate_kit(KIT, config_override=config)

    def test_legacy_command_list_is_rejected_instead_of_executed(self):
        self.assertIsNotNone(validate_kit)
        config = json.loads((KIT / 'docs/proyecto.json').read_text())
        config['validation']['required_checks'] = [{'id': 'unit', 'command': 'unreviewed'}]
        with self.assertRaises(ValueError):
            validate_kit(KIT, config_override=config)


if __name__ == '__main__':
    unittest.main()
