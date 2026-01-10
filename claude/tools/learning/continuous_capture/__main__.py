#!/usr/bin/env python3
"""
CLI entry point for continuous capture installer.

Allows running as: python3 -m claude.tools.learning.continuous_capture install
"""

from .installer import main

if __name__ == '__main__':
    main()
