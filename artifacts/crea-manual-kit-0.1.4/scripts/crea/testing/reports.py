"""Reportes estructurados: IDs reales JUnit y cobertura de líneas por archivo."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from .common import read


def junit(path, mapping):
    payload = Path(path).read_bytes()
    if len(payload) > 16_000_000 or b'<!DOCTYPE' in payload.upper() or b'<!ENTITY' in payload.upper():
        raise ValueError('UNSAFE_OR_OVERSIZED_XML')
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise ValueError('INVALID_JUNIT') from exc
    if root.tag not in ('testsuite', 'testsuites'):
        raise ValueError('INVALID_JUNIT_ROOT')
    cases = {}
    for case in root.iter('testcase'):
        name = case.get('name')
        if not name:
            raise ValueError('JUNIT_CASE_WITHOUT_ID')
        key = (case.get('classname', '') + '::' + name).lstrip(':')
        if key in cases:
            raise ValueError('DUPLICATE_JUNIT_ID')
        cases[key] = ('failed' if case.find('failure') is not None or case.find('error') is not None
                      else 'blocked' if case.find('skipped') is not None else 'passed')
    if not cases:
        raise ValueError('ZERO_TESTS')
    for suite in root.iter('testsuite'):
        descendants = list(suite.iter('testcase'))
        counts = {'tests': len(descendants), 'failures': sum(c.find('failure') is not None for c in descendants),
                  'errors': sum(c.find('error') is not None for c in descendants),
                  'skipped': sum(c.find('skipped') is not None for c in descendants)}
        for name, count in counts.items():
            if name in suite.attrib and int(suite.attrib[name]) != count:
                raise ValueError('JUNIT_COUNTER_MISMATCH')
    assertions = {}
    for criterion, ids in mapping.items():
        states = [cases.get(i, 'blocked') for i in ids]
        assertions[criterion] = ('passed' if states and all(x == 'passed' for x in states)
                                 else 'failed' if 'failed' in states else 'blocked')
    skipped = sum(x == 'blocked' for x in cases.values())
    return {'collected': len(cases), 'executed': len(cases) - skipped,
            'failed': sum(x == 'failed' for x in cases.values()), 'skipped': skipped,
            'assertions': assertions, 'test_ids': sorted(cases)}


def coverage(path, files, minimum):
    data = read(path)
    if not files or type(minimum) not in (float, int) or not 0 <= minimum <= 100:
        raise ValueError('INVALID_COVERAGE_REQUIREMENT')
    if not isinstance(data, dict) or not isinstance(data.get('files'), dict):
        raise ValueError('INVALID_COVERAGE_STRUCTURE')
    if any(not isinstance(k, str) or not isinstance(v, dict) for k, v in data['files'].items()):
        raise ValueError('INVALID_COVERAGE_FILE')
    normalized = {k.replace('\\', '/'): v for k, v in data['files'].items()}
    if len(normalized) != len(data['files']):
        raise ValueError('DUPLICATE_NORMALIZED_COVERAGE_FILE')
    counts, covered, total = {}, 0, 0
    for name in files:
        if name not in normalized:
            raise ValueError('COVERAGE_FILE_MISSING')
        row = normalized[name]
        for key in ('executed_lines', 'missing_lines'):
            lines = row.get(key)
            if not isinstance(lines, list) or any(type(x) is not int or x <= 0 for x in lines) or len(lines) != len(set(lines)):
                raise ValueError('INVALID_COVERAGE_LINE_NUMBERS')
        executed, missing = set(row['executed_lines']), set(row['missing_lines'])
        if executed & missing or not executed | missing:
            raise ValueError('INVALID_COVERAGE_LINES')
        size = len(executed | missing)
        percent = 100 * len(executed) / size
        counts[name] = percent
        total += size
        covered += len(executed)
    return {'passed': all(v >= minimum for v in counts.values()),
            'percent': 100 * covered / total, 'files': counts, 'minimum': minimum}
