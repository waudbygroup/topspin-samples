# -*- coding: utf-8 -*-
"""
Timeline Module
Handles timeline view showing samples and experiments chronologically
"""

import os
from datetime import datetime


class TimelineEntry:
    """Represents an entry in the timeline (sample or experiment)"""

    def __init__(self, entry_type, timestamp, name, details='', holder=None):
        """
        Args:
            entry_type: 'sample_created', 'sample_ejected', 'experiment'
            timestamp: datetime object
            name: Display name
            details: Additional information
            holder: Sample holder position (for experiments)
        """
        self.entry_type = entry_type
        self.timestamp = timestamp
        self.name = name
        self.details = details
        self.holder = holder  # Sample holder position
        self.filepath = None  # For experiments: full path to expno directory

    def get_sort_key(self):
        """Get sorting key for chronological ordering"""
        return self.timestamp

    def get_display_text(self):
        """Get formatted text for display"""
        time_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        if self.entry_type == 'sample_created':
            return "%s | Sample Created | %s" % (time_str, self.name)
        elif self.entry_type == 'sample_ejected':
            return "%s | Sample Ejected | %s" % (time_str, self.name)
        elif self.entry_type == 'experiment':
            return "%s | Experiment %s | %s" % (time_str, self.name, self.details)
        else:
            return "%s | %s" % (time_str, self.name)

    def __str__(self):
        """String representation for display in JList"""
        return self.get_display_text()

    def toString(self):
        """Java toString method for display in Swing components"""
        return self.get_display_text()


class TimelineBuilder:
    """Build timeline from samples and experiments in a directory"""

    def __init__(self, sample_io):
        """
        Args:
            sample_io: SampleIO instance for reading sample files
        """
        self.sample_io = sample_io

    def build_timeline(self, directory):
        """
        Build complete timeline for a directory

        Returns: List of TimelineEntry objects, sorted chronologically
        """
        entries = []

        # Add sample entries
        entries.extend(self._get_sample_entries(directory))

        # Add experiment entries
        entries.extend(self._get_experiment_entries(directory))

        # Sort chronologically
        entries.sort(key=lambda e: e.get_sort_key())

        return entries

    def _get_sample_entries(self, directory):
        """Get timeline entries from sample JSON files"""
        entries = []

        sample_files = self.sample_io.list_sample_files(directory)

        for filename in sample_files:
            filepath = os.path.join(directory, filename)

            try:
                data = self.sample_io.read_sample(filepath)
                metadata = data.get('Metadata', {})

                # Get sample label
                sample_label = data.get('Sample', {}).get('Label', 'Unknown')
                if not sample_label:
                    # Fall back to filename
                    _, label = self.sample_io.parse_filename(filename)
                    sample_label = label if label else 'Unknown'

                # Created entry
                created_ts = metadata.get('created_timestamp')
                if created_ts:
                    try:
                        dt = self._parse_iso_timestamp(created_ts)
                        entry = TimelineEntry('sample_created', dt, sample_label)
                        entry.filepath = filepath
                        entries.append(entry)
                    except ValueError:
                        pass

                # Ejected entry (if exists)
                ejected_ts = metadata.get('ejected_timestamp')
                if ejected_ts:
                    try:
                        dt = self._parse_iso_timestamp(ejected_ts)
                        entry = TimelineEntry('sample_ejected', dt, sample_label)
                        entry.filepath = filepath
                        entries.append(entry)
                    except ValueError:
                        pass

            except Exception as e:
                # Skip files that can't be read
                print("Warning: Could not read sample file %s: %s" % (filename, str(e)))
                continue

        return entries

    def _get_experiment_entries(self, directory):
        """
        Get timeline entries from experiment directories
        Experiment directories are integer-named folders containing 'acqus' file
        """
        entries = []

        if not os.path.isdir(directory):
            return entries

        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)

                # Check if it's a directory with integer name
                if os.path.isdir(item_path) and item.isdigit():
                    expno = int(item)

                    # Check for acqus file
                    acqus_path = os.path.join(item_path, 'acqus')
                    if os.path.isfile(acqus_path):
                        # Get timestamp from acqus file content (not modification time)
                        try:
                            dt = self._get_experiment_timestamp(acqus_path)

                            # If we couldn't extract timestamp from file, fall back to mtime
                            if dt is None:
                                mtime = os.path.getmtime(acqus_path)
                                dt = datetime.fromtimestamp(mtime)

                            # Try to get experiment details and holder from acqus
                            exp_details, holder = self._parse_acqus_info(acqus_path)

                            entry = TimelineEntry('experiment', dt, str(expno), exp_details, holder)
                            entry.filepath = item_path
                            entries.append(entry)

                        except (OSError, ValueError) as e:
                            print("Warning: Could not process experiment %s: %s" % (item, str(e)))
                            continue

        except OSError as e:
            print("Warning: Could not list directory %s: %s" % (directory, str(e)))

        return entries

    @staticmethod
    def _get_experiment_timestamp(acqus_path):
        """
        Extract experiment timestamp from acqus file

        Looks for a line like:
        $$ 2023-10-11 11:04:48.196 +0100  waudbyc@cl-nmr-spec701

        Returns datetime object or None if not found
        """
        import re

        try:
            with open(acqus_path, 'r') as f:
                for line in f:
                    # Look for timestamp pattern: $$ YYYY-MM-DD HH:MM:SS
                    match = re.search(r'\$\$\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
                    if match:
                        timestamp_str = match.group(1)
                        # Parse: 2023-10-11 11:04:48
                        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        return dt

            # Timestamp not found in file
            return None

        except Exception:
            return None

    @staticmethod
    def _parse_iso_timestamp(timestamp_str):
        """Parse ISO 8601 timestamp string to datetime object"""
        # Handle format: 2023-10-09T11:10:00.000Z
        # Remove 'Z' suffix and milliseconds for simplicity
        ts = timestamp_str.replace('Z', '').split('.')[0]
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")

    @staticmethod
    def _parse_acqus_info(acqus_path):
        """
        Parse acqus file to extract useful information
        Returns (summary_string, holder_position)
        """
        try:
            with open(acqus_path, 'r') as f:
                lines = f.readlines()

            info = {}

            # Look for key parameters
            for line in lines:
                line = line.strip()

                # PULPROG
                if line.startswith('##$PULPROG='):
                    value = line.split('=')[1].strip()
                    info['pulprog'] = value.strip('<>')

                # NUCLEUS (NUC1)
                elif line.startswith('##$NUC1='):
                    value = line.split('=')[1].strip()
                    info['nucleus'] = value.strip('<>')

                # Number of scans
                elif line.startswith('##$NS='):
                    value = line.split('=')[1].strip()
                    info['ns'] = value

                # Holder position
                elif line.startswith('##$HOLDER='):
                    value = line.split('=')[1].strip()
                    try:
                        info['holder'] = int(value)
                    except ValueError:
                        pass

            # Build summary
            parts = []
            if 'pulprog' in info:
                parts.append(info['pulprog'])
            if 'nucleus' in info:
                parts.append(info['nucleus'])
            if 'ns' in info:
                parts.append("%s scans" % info['ns'])

            summary = ", ".join(parts) if parts else "NMR experiment"
            holder = info.get('holder', None)

            return summary, holder

        except Exception:
            return "NMR experiment", None
