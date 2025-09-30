#!/usr/bin/env python3
"""
Quick start script for bank analysis.
Run this script to perform a complete analysis with default settings.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    from src.main import main
    main()