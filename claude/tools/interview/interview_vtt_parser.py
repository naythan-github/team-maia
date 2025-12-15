#!/usr/bin/env python3
"""
Interview VTT Parser

Parses VTT (Video Text Track) transcript files into structured segments.
Handles speaker extraction, timestamp parsing, and dialogue chunking.

Based on patterns from claude/tools/experimental/analyze_interview_vtt.py

Author: Maia System
Created: 2025-12-15 (Phase 223)
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import timedelta


@dataclass
class VTTSegment:
    """A single segment of VTT dialogue"""
    index: int
    speaker: str
    text: str
    speaker_role: str = "unknown"  # interviewer, candidate, unknown
    start_time_ms: Optional[int] = None
    end_time_ms: Optional[int] = None
    word_count: int = 0

    def __post_init__(self):
        self.word_count = len(self.text.split())


@dataclass
class ParsedInterview:
    """Complete parsed interview from VTT file"""
    file_path: str
    segments: List[VTTSegment] = field(default_factory=list)
    speakers: Dict[str, str] = field(default_factory=dict)  # speaker -> role
    total_duration_ms: Optional[int] = None
    interviewer: Optional[str] = None
    candidate: Optional[str] = None

    @property
    def total_segments(self) -> int:
        return len(self.segments)

    @property
    def total_words(self) -> int:
        return sum(s.word_count for s in self.segments)

    def get_candidate_text(self) -> str:
        """Get all candidate dialogue combined"""
        return ' '.join(
            s.text for s in self.segments
            if s.speaker_role == 'candidate'
        )

    def get_dialogue_by_speaker(self) -> Dict[str, List[str]]:
        """Group dialogue by speaker"""
        result = {}
        for segment in self.segments:
            if segment.speaker not in result:
                result[segment.speaker] = []
            result[segment.speaker].append(segment.text)
        return result


class InterviewVTTParser:
    """
    Parse VTT files into structured interview segments.

    VTT Format:
        WEBVTT

        00:00:00.000 --> 00:00:05.000
        <v Speaker Name>Dialogue text here</v>
    """

    # Regex patterns
    SPEAKER_PATTERN = re.compile(r'<v\s+([^>]+)>(.+?)</v>', re.DOTALL)
    TIMESTAMP_PATTERN = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})')

    # Known interviewer names (configurable)
    DEFAULT_INTERVIEWERS = ['Naythan', 'Naythan Dawe', 'Orro']

    def __init__(self, interviewer_names: Optional[List[str]] = None):
        """
        Initialize parser.

        Args:
            interviewer_names: List of known interviewer names to filter
        """
        self.interviewer_names = interviewer_names or self.DEFAULT_INTERVIEWERS

    def parse(self, vtt_path: str) -> ParsedInterview:
        """
        Parse a VTT file into structured segments.

        Args:
            vtt_path: Path to VTT file

        Returns:
            ParsedInterview with all segments and metadata
        """
        path = Path(vtt_path)
        if not path.exists():
            raise FileNotFoundError(f"VTT file not found: {vtt_path}")

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse all dialogue
        segments = self._extract_segments(content)

        # Identify speakers
        speakers = self._identify_speakers(segments)

        # Create result
        result = ParsedInterview(
            file_path=str(path.absolute()),
            segments=segments,
            speakers=speakers,
        )

        # Set interviewer and candidate
        for speaker, role in speakers.items():
            if role == 'interviewer':
                result.interviewer = speaker
            elif role == 'candidate':
                result.candidate = speaker

        # Calculate duration if timestamps available
        if segments and segments[-1].end_time_ms:
            result.total_duration_ms = segments[-1].end_time_ms

        return result

    def _extract_segments(self, content: str) -> List[VTTSegment]:
        """Extract all speaker segments from VTT content"""
        segments = []

        # Split by timestamp blocks
        blocks = re.split(r'\n\n+', content)

        current_start_ms = None
        current_end_ms = None
        segment_index = 0

        for block in blocks:
            # Skip header
            if block.strip().startswith('WEBVTT'):
                continue

            # Try to extract timestamp
            timestamp_match = self.TIMESTAMP_PATTERN.search(block)
            if timestamp_match:
                current_start_ms = self._parse_timestamp(timestamp_match.group(1))
                current_end_ms = self._parse_timestamp(timestamp_match.group(2))

            # Extract speaker dialogue
            speaker_matches = self.SPEAKER_PATTERN.findall(block)
            for speaker, text in speaker_matches:
                # Clean speaker name (handle pipe-separated metadata)
                speaker = speaker.split('|')[0].strip()
                text = text.strip()

                if text:  # Only add non-empty segments
                    segment = VTTSegment(
                        index=segment_index,
                        speaker=speaker,
                        text=text,
                        start_time_ms=current_start_ms,
                        end_time_ms=current_end_ms,
                    )
                    segments.append(segment)
                    segment_index += 1

        return segments

    def _identify_speakers(self, segments: List[VTTSegment]) -> Dict[str, str]:
        """
        Identify speaker roles (interviewer vs candidate).

        Uses heuristics:
        1. Known interviewer names
        2. Speaking frequency (interviewer usually asks more questions)
        """
        speakers = {}
        speaker_counts = {}

        for segment in segments:
            if segment.speaker not in speaker_counts:
                speaker_counts[segment.speaker] = 0
            speaker_counts[segment.speaker] += 1

        # First pass: check against known interviewer names
        for speaker in speaker_counts:
            is_interviewer = any(
                known.lower() in speaker.lower()
                for known in self.interviewer_names
            )
            if is_interviewer:
                speakers[speaker] = 'interviewer'
                segment.speaker_role = 'interviewer'

        # Second pass: remaining speakers are candidates
        for speaker in speaker_counts:
            if speaker not in speakers:
                speakers[speaker] = 'candidate'

        # Update segment roles
        for segment in segments:
            segment.speaker_role = speakers.get(segment.speaker, 'unknown')

        return speakers

    def _parse_timestamp(self, timestamp: str) -> int:
        """
        Parse VTT timestamp to milliseconds.

        Format: HH:MM:SS.mmm
        """
        parts = timestamp.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_ms = parts[2].split('.')
        seconds = int(seconds_ms[0])
        milliseconds = int(seconds_ms[1]) if len(seconds_ms) > 1 else 0

        total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds
        return total_ms

    def format_timestamp(self, ms: int) -> str:
        """Format milliseconds as HH:MM:SS"""
        td = timedelta(milliseconds=ms)
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def main():
    """CLI for testing VTT parser"""
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python3 interview_vtt_parser.py <vtt_file> [--json]")
        sys.exit(1)

    vtt_file = sys.argv[1]
    output_json = '--json' in sys.argv

    parser = InterviewVTTParser()

    try:
        result = parser.parse(vtt_file)

        if output_json:
            output = {
                'file_path': result.file_path,
                'total_segments': result.total_segments,
                'total_words': result.total_words,
                'interviewer': result.interviewer,
                'candidate': result.candidate,
                'speakers': result.speakers,
                'segments': [
                    {
                        'index': s.index,
                        'speaker': s.speaker,
                        'speaker_role': s.speaker_role,
                        'text': s.text,
                        'word_count': s.word_count,
                        'start_time_ms': s.start_time_ms,
                        'end_time_ms': s.end_time_ms,
                    }
                    for s in result.segments
                ]
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"VTT PARSE RESULT")
            print(f"{'='*60}")
            print(f"File: {result.file_path}")
            print(f"Total Segments: {result.total_segments}")
            print(f"Total Words: {result.total_words}")
            print(f"Interviewer: {result.interviewer}")
            print(f"Candidate: {result.candidate}")
            print(f"\nSpeakers: {result.speakers}")
            print(f"\nFirst 5 segments:")
            for s in result.segments[:5]:
                print(f"  [{s.index}] {s.speaker} ({s.speaker_role}): {s.text[:80]}...")

    except Exception as e:
        print(f"Error parsing VTT: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
