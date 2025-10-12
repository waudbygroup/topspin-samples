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
                return 'Metadata' in data and 'Sample' in data
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
            created = data.get('Metadata', {}).get('created_timestamp', '')

            # Extract label
            label = data.get('Sample', {}).get('Label', '')

            # Extract users
            users = data.get('Users', [])
            users_str = ', '.join(users) if users else ''

            # Extract sample components with labelling
            components = data.get('Sample', {}).get('Components', [])
            component_strs = []
            component_details = []
            for comp in components:
                if isinstance(comp, dict) and 'Name' in comp:
                    name = comp['Name']
                    labelling = comp.get('Isotopic labelling', '')

                    # Build display string
                    if labelling == 'custom':
                        custom = comp.get('Custom labelling', '')
                        if custom:
                            component_strs.append("%s (%s)" % (name, custom))
                        else:
                            component_strs.append(name)
                    elif labelling and labelling != 'unlabelled':
                        component_strs.append("%s (%s)" % (name, labelling))
                    else:
                        component_strs.append(name)

                    # Build tooltip detail string
                    conc = comp.get('Concentration', '')
                    unit = comp.get('Unit', '')
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
            buffer_data = data.get('Buffer', {})
            buffer_components = buffer_data.get('Components', [])
            buffer_parts = []
            buffer_details = []

            for comp in buffer_components:
                if isinstance(comp, dict) and 'name' in comp:
                    name = comp['name']
                    buffer_parts.append(name)

                    # Build tooltip detail
                    conc = comp.get('Concentration', '')
                    unit = comp.get('Unit', '')
                    if conc and unit:
                        buffer_details.append("%s: %s %s" % (name, conc, unit))
                    else:
                        buffer_details.append(name)

            # Add solvent
            solvent = buffer_data.get('Solvent', '')
            if solvent == 'custom':
                custom_solvent = buffer_data.get('Custom solvent', '')
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
            ref = buffer_data.get('Chemical shift reference', '')
            if ref and ref != 'none':
                ref_conc = buffer_data.get('Reference concentration', '')
                ref_unit = buffer_data.get('Reference unit', '')
                if ref_conc and ref_unit:
                    buffer_details.append("Reference: %s (%s %s)" % (ref, ref_conc, ref_unit))
                else:
                    buffer_details.append("Reference: %s" % ref)

            buffer_str = ', '.join(buffer_parts) if buffer_parts else ''
            buffer_tooltip = '\n'.join(buffer_details) if buffer_details else ''

            # Extract NMR tube information
            tube_data = data.get('NMR Tube', {})
            diameter = tube_data.get('Diameter', '')
            tube_type = tube_data.get('Type', '')
            tube_parts = []
            if diameter:
                tube_parts.append(diameter)
            if tube_type:
                tube_parts.append(tube_type)
            tube_str = ' '.join(tube_parts) if tube_parts else ''

            # Build tube tooltip with SampleJet info
            tube_details = []
            if diameter:
                tube_details.append("Diameter: %s" % diameter)
            if tube_type:
                tube_details.append("Type: %s" % tube_type)
            volume = tube_data.get('Sample Volume (μL)', '')
            if volume:
                tube_details.append("Volume: %s μL" % volume)
            sj_pos = tube_data.get('SampleJet Rack Position', '')
            if sj_pos:
                tube_details.append("SampleJet Position: %s" % sj_pos)
            sj_rack = tube_data.get('SampleJet Rack ID', '')
            if sj_rack:
                tube_details.append("SampleJet Rack: %s" % sj_rack)
            tube_tooltip = '\n'.join(tube_details) if tube_details else ''

            # Extract notes (first line for display)
            notes = data.get('Notes', '')
            notes_first_line = ''
            notes_tooltip = notes
            if notes:
                lines = notes.split('\n')
                notes_first_line = lines[0][:100]  # First 100 chars of first line
                if len(lines[0]) > 100:
                    notes_first_line += '...'

            # Extract lab reference for tooltip
            lab_ref = data.get('Laboratory Reference', {})
            labbook = lab_ref.get('Labbook Entry', '')
            exp_id = lab_ref.get('Experiment ID', '')
            label_details = []
            if labbook:
                label_details.append("Labbook: %s" % labbook)
            if exp_id:
                label_details.append("Experiment ID: %s" % exp_id)
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
                'components': components_str,
                'components_tooltip': components_tooltip,
                'buffer': buffer_str,
                'buffer_tooltip': buffer_tooltip,
                'tube': tube_str,
                'tube_tooltip': tube_tooltip,
                'notes': notes_first_line,
                'notes_tooltip': notes_tooltip,
                'experiment': experiment_folder
            }

        except Exception as e:
            # Error reading/parsing file - skip it
            return None
