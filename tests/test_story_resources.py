import hashlib
import json
from importlib.resources import files


def test_installed_story_resources_integrity_and_examples():
    from harness_core.story import ProviderBinding, StorySnapshot
    from harness_local.publication import PublicationRequest
    root = files('harness_local').joinpath('story_kit')
    manifest = json.loads(root.joinpath('manifest.json').read_bytes())
    for name, digest in manifest['files'].items():
        assert hashlib.sha256(root.joinpath(name).read_bytes()).hexdigest() == digest
    for model, name in [(ProviderBinding,'provider.json'), (PublicationRequest,'preview.json')]:
        model.model_validate(json.loads(root.joinpath(name).read_bytes()))
    stories = json.loads(root.joinpath('stories.json').read_bytes())
    assert len(stories) == 2
    for raw in stories: StorySnapshot.model_validate(raw)
    assert stories[0]['acceptance_sha256'] != stories[1]['acceptance_sha256']
