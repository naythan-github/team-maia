"""
Continuous Capture System for PAI Learning

Provides incremental, continuous learning capture that doesn't depend
on PreCompact hooks. Designed to survive context compaction.
"""

from .state_manager import CaptureStateManager
from .incremental_extractor import IncrementalExtractor
from .queue_writer import QueueWriter
from .queue_processor import QueueProcessor
from .daemon import ContinuousCaptureDaemon
from . import installer

__all__ = [
    'CaptureStateManager',
    'IncrementalExtractor',
    'QueueWriter',
    'QueueProcessor',
    'ContinuousCaptureDaemon',
    'installer'
]
