"""Validation-only pytest 9.1.1 emitter: give each subreport a unique JUnit case.

No test is suppressed and no XML is rewritten. The strict production parser is
unchanged. Parent IDs stay stable; subreports receive distinct IDs before emission.
"""
import pytest
from _pytest.subtests import SubtestReport

_sequence={}


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    if isinstance(report,SubtestReport):
        parent=report.nodeid
        number=_sequence.get(parent,0)+1
        _sequence[parent]=number
        report.nodeid=parent+f'[crea-subcase-{number}]'
