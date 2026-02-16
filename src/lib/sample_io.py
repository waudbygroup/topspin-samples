# -*- coding: utf-8 -*-
"""
Sample I/O Module
Handles JSON file operations for NMR sample metadata
"""

import json
import os
from datetime import datetime

# Import migration functionality
try:
    from migrate import update_to_latest_schema
    MIGRATION_AVAILABLE = True
except ImportError:
    MIGRATION_AVAILABLE = False


class SampleIO:
    """Handle reading/writing sample JSON files with proper timestamping"""

    def __init__(self, schema_version="0.1.0"):
        self.schema_version = schema_version

    @staticmethod
    def generate_filename(sample_label, timestamp=None):
        """
        Generate filename for new sample following convention:
        YYYY-MM-DD_HHMMSS_samplename.json

        Args:
            sample_label: Label for the sample
            timestamp: Optional datetime object to use (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        date_part = timestamp.strftime("%Y-%m-%d")
        time_part = timestamp.strftime("%H%M%S")

        # Sanitize sample label for filename
        safe_label = sample_label.replace(" ", "_")
        # Remove any characters that aren't alphanumeric, underscore, or hyphen
        safe_label = "".join(c for c in safe_label if c.isalnum() or c in "_-")

        if not safe_label:
            safe_label = "Sample"

        return "%s_%s_%s.json" % (date_part, time_part, safe_label)

    @staticmethod
    def parse_filename(filename):
        """
        Parse sample filename to extract timestamp and label
        Returns: (datetime_obj, sample_label) or (None, None) if invalid
        """
        if not filename.endswith('.json'):
            return None, None

        # Remove .json extension
        base = filename[:-5]

        # Expected format: YYYY-MM-DD_HHMMSS_label
        parts = base.split('_')
        if len(parts) < 3:
            return None, None

        try:
            date_str = parts[0]  # YYYY-MM-DD
            time_str = parts[1]  # HHMMSS
            label = "_".join(parts[2:])  # Rest is the label

            # Parse datetime
            datetime_str = "%s %s" % (date_str, time_str)
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H%M%S")

            return dt, label
        except ValueError:
            return None, None

    def read_sample(self, filepath, migrate=True):
        """
        Read sample JSON file and optionally migrate to latest schema

        Args:
            filepath: Path to JSON file
            migrate: If True, automatically migrate to latest schema version
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Apply migration if available and requested
            if migrate and MIGRATION_AVAILABLE:
                try:
                    data = update_to_latest_schema(data)
                except Exception as e:
                    # Log migration error but still return data
                    # Don't fail the read operation
                    pass

            return data
        except (IOError, ValueError) as e:
            raise Exception("Failed to read sample file %s: %s" % (filepath, str(e)))

    def write_sample(self, filepath, data, is_new=False):
        """
        Write sample JSON file with proper metadata timestamps

        Args:
            filepath: Full path to JSON file
            data: Sample data dictionary
            is_new: If True, sets created_timestamp; always updates modified_timestamp
        """
        # Ensure metadata section exists
        if 'metadata' not in data:
            data['metadata'] = {}

        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"

        # Set timestamps
        if is_new or 'created_timestamp' not in data['metadata']:
            data['metadata']['created_timestamp'] = now

        data['metadata']['modified_timestamp'] = now
        data['metadata']['schema_version'] = self.schema_version

        # Write JSON file
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            raise Exception("Failed to write sample file %s: %s" % (filepath, str(e)))

    def eject_sample(self, filepath):
        """Add ejected timestamp to sample"""
        data = self.read_sample(filepath)

        if 'metadata' not in data:
            data['metadata'] = {}

        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"
        data['metadata']['ejected_timestamp'] = now
        data['metadata']['modified_timestamp'] = now

        self.write_sample(filepath, data, is_new=False)

    def get_sample_status(self, filepath):
        """
        Check if sample is loaded (active) or ejected
        Returns: 'loaded', 'ejected', or 'unknown'
        """
        try:
            data = self.read_sample(filepath)

            if 'metadata' in data and data['metadata'].get('ejected_timestamp'):
                return 'ejected'
            else:
                return 'loaded'  # Active/loaded sample
        except Exception:
            return 'unknown'

    @staticmethod
    def list_sample_files(directory):
        """
        List all sample JSON files in directory
        Returns list of filenames matching timestamp pattern, sorted chronologically
        """
        if not os.path.isdir(directory):
            return []

        sample_files = []

        try:
            for filename in os.listdir(directory):
                if filename.endswith('.json'):
                    dt, label = SampleIO.parse_filename(filename)
                    if dt is not None:
                        sample_files.append(filename)
        except OSError:
            return []

        # Sort chronologically (filename format ensures alphabetical = chronological)
        sample_files.sort()

        return sample_files

    def find_active_sample(self, directory):
        """
        Find the active sample in directory (most recent without ejected_timestamp)
        Returns: filename or None
        """
        sample_files = self.list_sample_files(directory)

        # Check from most recent backwards
        for filename in reversed(sample_files):
            filepath = os.path.join(directory, filename)
            status = self.get_sample_status(filepath)
            if status == 'loaded':  # Active sample
                return filename

        return None

    def auto_eject_active_sample(self, directory):
        """
        Automatically eject any active sample in the directory
        Returns: filename of ejected sample or None
        """
        active_sample = self.find_active_sample(directory)

        if active_sample:
            filepath = os.path.join(directory, active_sample)
            self.eject_sample(filepath)
            return active_sample

        return None
