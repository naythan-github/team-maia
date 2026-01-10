#!/usr/bin/env python3
"""
Daemon Runner Script

Sets up PYTHONPATH and runs the continuous capture daemon.
This script ensures proper module imports when run by LaunchAgent.
"""

import sys
from pathlib import Path

# Add MAIA_ROOT to sys.path before any imports
MAIA_ROOT = Path(__file__).parent.parent.parent.parent.parent
if str(MAIA_ROOT) not in sys.path:
    sys.path.insert(0, str(MAIA_ROOT))

# Now we can import the daemon
from claude.tools.learning.continuous_capture.daemon import ContinuousCaptureDaemon

def main():
    """Run the continuous capture daemon."""
    daemon = ContinuousCaptureDaemon()
    daemon.run()

if __name__ == '__main__':
    main()
