# -*- coding: utf-8 -*-
"""
Timeline Module
Handles timeline view showing samples and experiments chronologically
"""

import os
from datetime import datetime


class TimelineEntry:
    """Represents an entry in the timeline (sample or experiment)"""

    def __init__(self, entry_type, timestamp, name, details='', holder=None, parmod=None):
        """
        Args:
            entry_type: 'sample_created', 'sample_ejected', 'experiment'
            timestamp: datetime object
            name: Display name
            details: Additional information
            holder: Sample holder position (for experiments)
            parmod: PARMOD value (dimensions - 1) for experiments
        """
        self.entry_type = entry_type
        self.timestamp = timestamp
        self.name = name
        self.details = details
        self.holder = holder  # Sample holder position
        self.parmod = parmod  # PARMOD value (dimensions = parmod + 1)
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
                metadata = data.get('metadata', {})

                # Get sample label
                sample_label = data.get('sample', {}).get('label', 'Unknown')
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
        Experiment directories are integer-named folders containing 'acqu' file
        Only experiments with 'acqus' file (i.e., acquired) are included in timeline
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

                    # Check for acqu file (indicates valid experiment directory)
                    acqu_path = os.path.join(item_path, 'acqu')
                    acqus_path = os.path.join(item_path, 'acqus')

                    if os.path.isfile(acqu_path):
                        # Check if experiment has been acquired (has acqus file)
                        if os.path.isfile(acqus_path):
                            # Acquired experiment - get timestamp from acqus file
                            try:
                                dt = self._get_experiment_timestamp(acqus_path)

                                # If we couldn't extract timestamp from file, fall back to mtime
                                if dt is None:
                                    mtime = os.path.getmtime(acqus_path)
                                    # Convert to naive UTC datetime for consistency with other timestamps
                                    dt = datetime.utcfromtimestamp(mtime)

                                # Try to get experiment details, holder, and parmod from acqus
                                exp_details, holder, parmod = self._parse_acqus_info(acqus_path)

                                entry = TimelineEntry('experiment', dt, str(expno), exp_details, holder, parmod)
                                entry.filepath = item_path
                                entries.append(entry)

                            except (OSError, ValueError) as e:
                                print("Warning: Could not process experiment %s: %s" % (item, str(e)))
                                continue
                        # else: experiment not yet acquired (no acqus file) - skip for timeline

        except OSError as e:
            print("Warning: Could not list directory %s: %s" % (directory, str(e)))

        return entries

    @staticmethod
    def _get_experiment_timestamp(acqus_path):
        """
        Extract experiment timestamp from acqus file.

        Reads ##$DATE= Unix timestamp (e.g. ##$DATE= 1483480402).
        Falls back to file mtime if not found.

        Returns datetime object (UTC) or None if not found
        """
        try:
            with open(acqus_path, 'r') as f:
                for line in f:
                    if line.startswith('##$DATE='):
                        value = line.split('=')[1].strip()
                        unix_ts = int(value)
                        return datetime.utcfromtimestamp(unix_ts)

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
        Returns (summary_string, holder_position, parmod)
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

                # PARMOD (dimensions - 1)
                elif line.startswith('##$PARMODE='):
                    value = line.split('=')[1].strip()
                    try:
                        info['parmod'] = int(value)
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
            parmod = info.get('parmod', None)

            return summary, holder, parmod

        except Exception:
            return "NMR experiment", None, None
