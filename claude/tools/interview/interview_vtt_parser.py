#!/usr/bin/env python3
"""Interview VTT Parser - TDD Implementation"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class VTTSegment:
    """A single segment of VTT dialogue"""
    index: int
    speaker: str
    text: str
    speaker_role: str = "unknown"
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
    speakers: Dict[str, str] = field(default_factory=dict)
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
        return ' '.join(s.text for s in self.segments if s.speaker_role == 'candidate')

    def get_dialogue_by_speaker(self) -> Dict[str, List[str]]:
        result = {}
        for segment in self.segments:
            if segment.speaker not in result:
                result[segment.speaker] = []
            result[segment.speaker].append(segment.text)
        return result


class InterviewVTTParser:
    """Parse VTT files - TDD stub"""

    # Pattern for labeled speakers: <v Speaker Name>text</v>
    SPEAKER_PATTERN = re.compile(r'<v\s+([^>]+)>(.+?)</v>', re.DOTALL)
    # Pattern for unlabeled speakers: <v >text</v> (common for external participants)
    UNLABELED_PATTERN = re.compile(r'<v\s*>(.+?)</v>', re.DOTALL)
    DEFAULT_INTERVIEWERS = ['Naythan', 'Naythan Dawe', 'Orro']

    def __init__(self, interviewer_names: Optional[List[str]] = None):
        self.interviewer_names = interviewer_names or self.DEFAULT_INTERVIEWERS

    def parse(self, vtt_path: str) -> ParsedInterview:
        """Parse VTT file - implemented to pass test_parse_vtt_file and test_file_not_found"""
        from pathlib import Path
        path = Path(vtt_path)

        if not path.exists():
            raise FileNotFoundError(f"VTT file not found: {vtt_path}")

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        segments = self._extract_segments(content)
        speakers = self._identify_speakers(segments)

        result = ParsedInterview(
            file_path=str(path.absolute()),
            segments=segments,
            speakers=speakers,
        )

        for speaker, role in speakers.items():
            if role == 'interviewer':
                result.interviewer = speaker
            elif role == 'candidate':
                result.candidate = speaker

        if segments and segments[-1].end_time_ms:
            result.total_duration_ms = segments[-1].end_time_ms

        return result

    def _extract_segments(self, content: str) -> List[VTTSegment]:
        """Extract segments from VTT content"""
        TIMESTAMP_PATTERN = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})')
        segments = []
        blocks = re.split(r'\n\n+', content)
        current_start_ms = None
        current_end_ms = None
        segment_index = 0

        for block in blocks:
            if block.strip().startswith('WEBVTT'):
                continue

            timestamp_match = TIMESTAMP_PATTERN.search(block)
            if timestamp_match:
                current_start_ms = self._parse_timestamp(timestamp_match.group(1))
                current_end_ms = self._parse_timestamp(timestamp_match.group(2))

            # First, extract labeled speakers
            speaker_matches = self.SPEAKER_PATTERN.findall(block)
            for speaker, text in speaker_matches:
                speaker = speaker.split('|')[0].strip()
                text = text.strip()
                if text and speaker:  # Skip if speaker is empty (handled below)
                    segment = VTTSegment(
                        index=segment_index,
                        speaker=speaker,
                        text=text,
                        start_time_ms=current_start_ms,
                        end_time_ms=current_end_ms,
                    )
                    segments.append(segment)
                    segment_index += 1

            # Also extract unlabeled speakers (external participants like candidates)
            unlabeled_matches = self.UNLABELED_PATTERN.findall(block)
            for text in unlabeled_matches:
                text = text.strip()
                if text:
                    segment = VTTSegment(
                        index=segment_index,
                        speaker="[Candidate]",  # Default label for unlabeled external participants
                        text=text,
                        start_time_ms=current_start_ms,
                        end_time_ms=current_end_ms,
                    )
                    segments.append(segment)
                    segment_index += 1

        return segments

    def _parse_timestamp(self, timestamp: str) -> int:
        """Parse timestamp - implemented to pass test_timestamp_parsing"""
        parts = timestamp.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_ms = parts[2].split('.')
        seconds = int(seconds_ms[0])
        milliseconds = int(seconds_ms[1]) if len(seconds_ms) > 1 else 0
        return (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds

    def _identify_speakers(self, segments: List[VTTSegment]) -> Dict[str, str]:
        """Identify speakers - implemented to pass test_identify_interviewer"""
        speakers = {}
        speaker_counts = {}

        for segment in segments:
            if segment.speaker not in speaker_counts:
                speaker_counts[segment.speaker] = 0
            speaker_counts[segment.speaker] += 1

        for speaker in speaker_counts:
            is_interviewer = any(
                known.lower() in speaker.lower()
                for known in self.interviewer_names
            )
            if is_interviewer:
                speakers[speaker] = 'interviewer'

        for speaker in speaker_counts:
            if speaker not in speakers:
                speakers[speaker] = 'candidate'

        for segment in segments:
            segment.speaker_role = speakers.get(segment.speaker, 'unknown')

        return speakers
