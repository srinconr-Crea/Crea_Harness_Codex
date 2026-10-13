"""Synthetic worker function for exact decimals, nulls and empty input."""
from decimal import Decimal


def total(values):
    return str(sum((Decimal(value) for value in values if value is not None),Decimal('0.00')))
