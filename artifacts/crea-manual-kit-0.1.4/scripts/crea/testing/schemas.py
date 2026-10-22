"""Validación Draft2020-12 offline; nunca resolver referencias remotas."""
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry
from referencing.exceptions import NoSuchResource
from .common import ASSETS, KIT, read


def no_remote(uri):
    raise NoSuchResource(ref=uri)


def validate_schema(schema, instance):
    Draft202012Validator.check_schema(schema)
    checker = FormatChecker()
    if 'date-time' not in checker.checkers:
        raise ValueError('SCHEMA_DATETIME_DEPENDENCY_MISSING_INSTALL_REQUIREMENTS')
    validator = Draft202012Validator(schema, format_checker=checker,
                                     registry=Registry(retrieve=no_remote))
    errors = sorted(validator.iter_errors(instance), key=lambda e: str(list(e.path)))
    if errors:
        e = errors[0]
        # Do not copy values of rejected configuration into logs.
        raise ValueError('SCHEMA_INVALID: ' + '/'.join(map(str, e.path)) + ':' + str(e.validator))
    return instance


def validate(kind, instance):
    path = KIT / 'docs/proyecto.schema.json' if kind == 'project' else ASSETS / (kind + '.schema.json')
    return validate_schema(read(path), instance)
