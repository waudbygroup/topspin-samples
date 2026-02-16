# -*- coding: utf-8 -*-
"""
Sample Scanner
Efficiently scans directory trees for NMR sample JSON files
"""

import os
import json


class SampleScanner:
    """Scan directory trees for sample files with optimization"""

    def __init__(self, sample_io):
        """Initialize scanner

        Args:
            sample_io: SampleIO instance for file operations
        """
        self.sample_io = sample_io

    def scan_roots(self, root_directories):
        """Scan multiple root directories for samples

        Args:
            root_directories: List of directory paths to scan

        Returns:
            list: List of sample info dictionaries
        """
        all_samples = []

        for root in root_directories:
            if os.path.exists(root) and os.path.isdir(root):
                samples = self._scan_directory(root)
                all_samples.extend(samples)

        return all_samples

    def _scan_directory(self, directory):
        """Recursively scan a directory for samples with optimization

        Args:
            directory: Directory path to scan

        Returns:
            list: List of sample info dictionaries
        """
        samples = []

        try:
            # List all items in directory
            items = os.listdir(directory)

            # Check for sample files in this directory
            sample_files = [f for f in items if f.endswith('.json') and
                           self._is_sample_file(os.path.join(directory, f))]

            if sample_files:
                # Found sample files - process them and stop descent
                for filename in sample_files:
                    filepath = os.path.join(directory, filename)
                    sample_info = self._extract_sample_info(filepath)
                    if sample_info:
                        samples.append(sample_info)
                # Don't descend further - samples found at this level
                return samples

            # No sample files found - check if this is an experiment directory
            # Experiment directories contain numbered folders with 'acqu' files
            has_experiment = False
            for item in items:
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    # Check if this is a numbered experiment folder
                    try:
                        int(item)  # Experiment folders are numbered
                        # Check for acqu file
                        if os.path.exists(os.path.join(item_path, 'acqu')):
                            has_experiment = True
                            break
                    except ValueError:
                        # Not a numbered folder
                        pass

            if has_experiment:
                # This directory contains experiment folders - don't descend further
                return samples

            # Recurse into subdirectories
            for item in items:
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    # Skip hidden directories and common non-data directories
                    if not item.startswith('.') and item not in ['pdata', 'ser']:
                        child_samples = self._scan_directory(item_path)
                        samples.extend(child_samples)

        except (OSError, IOError):
            # Permission denied or other error - skip this directory
            pass

        return samples

    def _is_sample_file(self, filepath):
        """Check if file is a valid sample JSON file

        Args:
            filepath: Path to file

        Returns:
            bool: True if valid sample file
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Check if it has the expected structure
                return 'metadata' in data and 'sample' in data
        except:
            return False

    def _extract_sample_info(self, filepath):
        """Extract relevant information from sample file

        Args:
            filepath: Path to sample JSON file

        Returns:
            dict: Sample information or None if error
        """
        try:
            data = self.sample_io.read_sample(filepath)

            # Extract creation date
            created = data.get('metadata', {}).get('created_timestamp', '')

            # Extract label
            label = data.get('sample', {}).get('label', '')

            # Extract users and groups
            people = data.get('people', {})
            users = people.get('users', [])
            groups = people.get('groups', [])
            users_str = ', '.join(users) if users else ''

            # Build users tooltip with groups
            users_tooltip_parts = []
            if users:
                users_tooltip_parts.append("Users: %s" % ', '.join(users))
            if groups:
                users_tooltip_parts.append("Groups: %s" % ', '.join(groups))
            users_tooltip = '\n'.join(users_tooltip_parts) if users_tooltip_parts else ''

            # Extract sample components with labelling
            components = data.get('sample', {}).get('components', [])
            component_strs = []
            component_details = []
            for comp in components:
                if isinstance(comp, dict) and 'name' in comp:
                    name = comp['name']
                    labelling = comp.get('isotopic_labelling', '')

                    # Build display string
                    if labelling == 'custom':
                        custom = comp.get('custom_labelling', '')
                        if custom:
                            component_strs.append("%s (%s)" % (name, custom))
                        else:
                            component_strs.append(name)
                    elif labelling and labelling != 'unlabelled':
                        component_strs.append("%s (%s)" % (name, labelling))
                    else:
                        component_strs.append(name)

                    # Build tooltip detail string
                    # Use new field name 'concentration_or_amount' (v0.1.0+)
                    conc = comp.get('concentration_or_amount', comp.get('concentration', ''))
                    unit = comp.get('unit', '')
                    if conc and unit:
                        detail = "%s: %s %s" % (name, conc, unit)
                    else:
                        detail = name
                    if labelling and labelling != 'unlabelled':
                        detail += " [%s]" % labelling
                    component_details.append(detail)

            components_str = ', '.join(component_strs) if component_strs else ''
            components_tooltip = '\n'.join(component_details) if component_details else ''

            # Extract buffer components, solvent, and pH
            buffer_data = data.get('buffer', {})
            buffer_components = buffer_data.get('components', [])
            buffer_parts = []
            buffer_details = []

            for comp in buffer_components:
                if isinstance(comp, dict) and 'name' in comp:
                    name = comp['name']
                    buffer_parts.append(name)

                    # Build tooltip detail
                    conc = comp.get('concentration', '')
                    unit = comp.get('unit', '')
                    if conc and unit:
                        buffer_details.append("%s: %s %s" % (name, conc, unit))
                    else:
                        buffer_details.append(name)

            # Add solvent
            solvent = buffer_data.get('solvent', '')
            if solvent == 'custom':
                custom_solvent = buffer_data.get('custom_solvent', '')
                if custom_solvent:
                    buffer_parts.append(custom_solvent)
                    buffer_details.append("Solvent: %s" % custom_solvent)
            elif solvent:
                buffer_parts.append(solvent)
                buffer_details.append("Solvent: %s" % solvent)

            # Add pH
            ph = buffer_data.get('pH', '')
            if ph:
                buffer_parts.append("pH %s" % ph)
                buffer_details.append("pH: %s" % ph)

            # Add chemical shift reference
            ref = buffer_data.get('chemical_shift_reference', '')
            if ref and ref != 'none':
                ref_conc = buffer_data.get('reference_concentration', '')
                ref_unit = buffer_data.get('reference_unit', '')
                if ref_conc and ref_unit:
                    buffer_details.append("Reference: %s (%s %s)" % (ref, ref_conc, ref_unit))
                else:
                    buffer_details.append("Reference: %s" % ref)

            buffer_str = ', '.join(buffer_parts) if buffer_parts else ''
            buffer_tooltip = '\n'.join(buffer_details) if buffer_details else ''

            # Extract NMR tube information
            tube_data = data.get('nmr_tube', {})
            diameter = tube_data.get('diameter', '')
            tube_type = tube_data.get('type', '')
            tube_parts = []
            if diameter:
                # Format diameter value (now numeric in v0.1.0)
                if isinstance(diameter, (int, float)):
                    tube_parts.append("%.1f mm" % diameter)
                else:
                    tube_parts.append(str(diameter))
            if tube_type:
                tube_parts.append(tube_type)
            tube_str = ' '.join(tube_parts) if tube_parts else ''

            # Build tube tooltip with SampleJet info
            tube_details = []
            if diameter:
                if isinstance(diameter, (int, float)):
                    tube_details.append("Diameter: %.1f mm" % diameter)
                else:
                    tube_details.append("Diameter: %s" % diameter)
            if tube_type:
                tube_details.append("Type: %s" % tube_type)
            volume = tube_data.get('sample_volume_uL', '')
            if volume:
                tube_details.append("Volume: %s uL" % volume)
            mass = tube_data.get('sample_mass_mg', '')
            if mass:
                tube_details.append("Mass: %s mg" % mass)
            # Use new field name 'rack_id' (v0.1.0+), fall back to old name
            sj_rack = tube_data.get('rack_id', tube_data.get('samplejet_rack_id', ''))
            if sj_rack:
                tube_details.append("Rack ID: %s" % sj_rack)
            rotor_serial = tube_data.get('rotor_serial', '')
            if rotor_serial:
                tube_details.append("Rotor Serial: %s" % rotor_serial)
            tube_tooltip = '\n'.join(tube_details) if tube_details else ''

            # Extract notes (first line for display)
            notes = data.get('notes', '')
            notes_first_line = ''
            notes_tooltip = notes
            if notes:
                lines = notes.split('\n')
                notes_first_line = lines[0][:100]  # First 100 chars of first line
                if len(lines[0]) > 100:
                    notes_first_line += '...'

            # Extract lab reference for tooltip
            lab_ref = data.get('reference', {})
            sample_id = lab_ref.get('sample_id', '')
            labbook = lab_ref.get('labbook_entry', '')
            label_details = []
            if sample_id:
                label_details.append("Sample ID: %s" % sample_id)
            if labbook:
                label_details.append("Labbook: %s" % labbook)
            label_tooltip = '\n'.join(label_details) if label_details else ''

            # Get directory (parent of sample file) and extract experiment folder name
            directory = os.path.dirname(filepath)
            experiment_folder = os.path.basename(directory)

            return {
                'filepath': filepath,
                'directory': directory,
                'filename': os.path.basename(filepath),
                'created': created,
                'label': label,
                'label_tooltip': label_tooltip,
                'users': users_str,
                'users_tooltip': users_tooltip,
                'components': components_str,
                'components_tooltip': components_tooltip,
                'buffer': buffer_str,
                'buffer_tooltip': buffer_tooltip,
                'tube': tube_str,
                'tube_tooltip': tube_tooltip,
                'notes': notes_first_line,
                'notes_tooltip': notes_tooltip,
                'experiment': experiment_folder,
                'experiment_tooltip': directory
            }

        except Exception as e:
            # Error reading/parsing file - skip it
            # Debug: print error to help troubleshoot
            import sys
            print >> sys.stderr, "Error parsing %s: %s" % (filepath, str(e))
            return None
