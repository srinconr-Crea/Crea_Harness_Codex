#!/usr/bin/env python3
"""Portable CLI entry point; no Azure SDK dependency."""
from integrations.azure_devops_context import main

if __name__ == '__main__':
    raise SystemExit(main())
