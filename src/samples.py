# -*- coding: utf-8 -*-
"""
NMR Sample Manager - Main GUI Application
Persistent Jython/Swing application for managing NMR sample metadata in TopSpin
"""

from javax.swing import *
from javax.swing.table import DefaultTableModel, AbstractTableModel, DefaultTableCellRenderer
from java.awt import *
from java.awt.event import MouseAdapter, KeyEvent
from javax.swing import AbstractAction, KeyStroke, JComponent
from java.lang import System
import java.awt.event
import sys
import os

# Add lib directory to path - use script directory fallback since __file__ may not be defined in Jython
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Fallback for Jython when __file__ is not defined
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

lib_path = os.path.join(script_dir, 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from sample_io import SampleIO
from schema_form import SchemaFormGenerator
from timeline import TimelineBuilder

APP_KEY = "topspin.nmr.sample.manager"


class SampleManagerApp:
    """Main sample manager application using singleton pattern"""

    def __init__(self):
        # State variables
        self.current_directory = None
        self.sample_io = SampleIO()

        # Get script directory for schema path
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

        self.script_dir = script_dir
        self.current_schema_path = os.path.join(script_dir, 'schemas', 'current.json')
        self.form_generator = None
        self.current_sample_file = None
        self.timeline_builder = TimelineBuilder(self.sample_io)
        self.form_modified = False  # Track if form has been edited

        # GUI components
        self.frame = None
        self.status_label = None
        self.dir_label = None
        self.sample_table = None
        self.sample_table_model = None
        self.btn_new = None
        self.btn_duplicate = None
        self.btn_edit = None
        self.btn_save = None
        self.btn_cancel = None
        self.form_panel = None
        self.timeline_table = None
        self.timeline_table_model = None
        self.tabbed_pane = None
        self.selected_sample_filepath = None

        # Initialize
        self._create_gui()
        self._set_initial_button_states()
        self._navigate_to_curdata()

    def _set_initial_button_states(self):
        """Set initial button enabled/disabled states"""
        self.btn_duplicate.setEnabled(False)
        self.btn_edit.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.btn_cancel.setEnabled(False)

    def mark_form_modified(self):
        """Mark form as modified and enable Save/Cancel buttons"""
        if not self.form_modified:
            self.form_modified = True
            self.btn_save.setEnabled(True)
            self.btn_cancel.setEnabled(True)

    def _get_git_version(self):
        """Get git commit hash for version display"""
        try:
            import subprocess
            # Get short commit hash
            result = subprocess.check_output(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=self.script_dir,
                stderr=subprocess.STDOUT
            )
            return result.strip()
        except:
            return None

    def _create_gui(self):
        """Build the GUI"""
        # Get git version for window title
        git_version = self._get_git_version()
        title = "NMR Sample Manager"
        if git_version:
            title = "%s (version ref: %s)" % (title, git_version)

        self.frame = JFrame(title)
        self.frame.setSize(900, 700)
        self.frame.setDefaultCloseOperation(WindowConstants.HIDE_ON_CLOSE)

        # Main container
        container = self.frame.getContentPane()
        container.setLayout(BorderLayout())

        # Left-right split
        split_pane = JSplitPane(JSplitPane.HORIZONTAL_SPLIT)
        split_pane.setDividerLocation(300)

        # Left - sample list
        list_panel = self._create_sample_list_panel()
        split_pane.setLeftComponent(list_panel)

        # Right - tabbed pane with Sample Details and Timeline
        self.tabbed_pane = JTabbedPane()

        # Tab 1: Sample Details
        form_view = self._create_form_view()
        self.tabbed_pane.addTab("Sample Details", form_view)

        # Tab 2: Timeline
        timeline_view = self._create_timeline_view()
        self.tabbed_pane.addTab("Timeline", timeline_view)

        split_pane.setRightComponent(self.tabbed_pane)
        container.add(split_pane, BorderLayout.CENTER)

        # Bottom panel - status bar
        status_panel = self._create_status_panel()
        container.add(status_panel, BorderLayout.SOUTH)

        self.frame.setVisible(True)

    def _create_top_panel(self):
        """Create top panel with directory navigation - REMOVED, now in left panel"""
        # This panel is now removed - directory browser moved to left panel
        return None

    def _create_sample_list_panel(self):
        """Create left panel with directory browser, action buttons, and sample list"""
        panel = JPanel(BorderLayout())
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10))

        # Top section container
        top_section = JPanel()
        top_section.setLayout(BoxLayout(top_section, BoxLayout.Y_AXIS))

        # Directory browser section
        dir_panel = JPanel()
        dir_panel.setLayout(BoxLayout(dir_panel, BoxLayout.Y_AXIS))
        dir_panel.setBorder(BorderFactory.createEmptyBorder(0, 0, 10, 0))

        # Directory label
        dir_label_text = JLabel("Current Directory:")
        dir_label_text.setFont(dir_label_text.getFont().deriveFont(Font.BOLD, 11.0))
        dir_label_text.setAlignmentX(Component.LEFT_ALIGNMENT)
        dir_panel.add(dir_label_text)

        dir_panel.add(Box.createVerticalStrut(3))

        # Directory path (full width)
        self.dir_label = JTextField("None")
        self.dir_label.setEditable(False)
        self.dir_label.setBackground(Color.WHITE)
        self.dir_label.setMaximumSize(Dimension(32767, 28))
        self.dir_label.setAlignmentX(Component.LEFT_ALIGNMENT)
        dir_panel.add(self.dir_label)

        dir_panel.add(Box.createVerticalStrut(3))

        # Browse button on separate line
        browse_panel = JPanel(FlowLayout(FlowLayout.LEFT, 0, 0))
        browse_panel.setAlignmentX(Component.LEFT_ALIGNMENT)
        btn_browse = JButton('Browse...')
        btn_browse.setPreferredSize(Dimension(100, 28))
        btn_browse.addActionListener(lambda e: self._browse_directory())
        browse_panel.add(btn_browse)
        dir_panel.add(browse_panel)

        top_section.add(dir_panel)

        # Action buttons section
        button_panel = JPanel(FlowLayout(FlowLayout.LEFT, 5, 5))
        button_panel.setAlignmentX(Component.LEFT_ALIGNMENT)
        button_panel.setBorder(BorderFactory.createEmptyBorder(5, 0, 10, 0))

        # Store button references for enabling/disabling
        self.btn_new = JButton('New Sample')
        self.btn_duplicate = JButton('Duplicate')
        self.btn_edit = JButton('Edit')

        self.btn_new.setPreferredSize(Dimension(110, 28))
        self.btn_duplicate.setPreferredSize(Dimension(110, 28))
        self.btn_edit.setPreferredSize(Dimension(110, 28))

        self.btn_new.addActionListener(lambda e: self._new_sample())
        self.btn_duplicate.addActionListener(lambda e: self._duplicate_sample())
        self.btn_edit.addActionListener(lambda e: self._edit_sample())

        self.btn_new.setToolTipText("Create a new sample (auto-ejects active sample)")
        self.btn_duplicate.setToolTipText("Duplicate the selected sample")
        self.btn_edit.setToolTipText("Edit the selected sample")

        button_panel.add(self.btn_new)
        button_panel.add(self.btn_duplicate)
        button_panel.add(self.btn_edit)

        top_section.add(button_panel)

        # Set preferred and maximum height to ensure buttons are always visible
        top_section.setPreferredSize(Dimension(250, 145))
        top_section.setMinimumSize(Dimension(200, 145))
        top_section.setMaximumSize(Dimension(32767, 145))

        panel.add(top_section, BorderLayout.NORTH)

        # Sample table
        self.sample_table_model = SampleTableModel()
        self.sample_table = JTable(self.sample_table_model)
        self.sample_table.setSelectionMode(ListSelectionModel.SINGLE_SELECTION)
        self.sample_table.setRowHeight(30)
        self.sample_table.setShowGrid(False)
        self.sample_table.setIntercellSpacing(Dimension(0, 0))

        # Configure columns
        col_model = self.sample_table.getColumnModel()
        col_model.getColumn(0).setPreferredWidth(30)
        col_model.getColumn(0).setMaxWidth(30)
        col_model.getColumn(1).setPreferredWidth(170)

        # Custom renderer for status icons
        self.sample_table.setDefaultRenderer(Object, SampleTableCellRenderer())

        # Selection listener
        self.sample_table.getSelectionModel().addListSelectionListener(
            lambda e: self._on_sample_selected() if not e.getValueIsAdjusting() else None)

        # Context menu
        self.sample_table.addMouseListener(SampleTableMouseListener(self))

        scroll_pane = JScrollPane(self.sample_table)
        panel.add(scroll_pane, BorderLayout.CENTER)

        return panel

    def _create_form_view(self):
        """Create form view panel with improved layout"""
        panel = JPanel(BorderLayout())
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10))

        # Placeholder for form (will be replaced with actual form)
        self.form_panel = JPanel()
        self.form_panel.setLayout(BorderLayout())
        placeholder = JLabel("Select a sample or create a new one", JLabel.CENTER)
        placeholder.setFont(placeholder.getFont().deriveFont(Font.ITALIC, 12.0))
        self.form_panel.add(placeholder, BorderLayout.CENTER)

        # Add Escape key binding to cancel
        input_map = panel.getInputMap(JComponent.WHEN_ANCESTOR_OF_FOCUSED_COMPONENT)
        action_map = panel.getActionMap()
        input_map.put(KeyStroke.getKeyStroke(KeyEvent.VK_ESCAPE, 0), "cancel")
        action_map.put("cancel", CancelAction(self))

        panel.add(self.form_panel, BorderLayout.CENTER)

        # Button panel for form actions - fixed at bottom with clear styling
        form_button_panel = JPanel(BorderLayout())
        form_button_panel.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createMatteBorder(1, 0, 0, 0, Color.LIGHT_GRAY),
            BorderFactory.createEmptyBorder(10, 10, 10, 10)
        ))

        button_row = JPanel(FlowLayout(FlowLayout.RIGHT, 10, 0))
        self.btn_cancel = JButton('Cancel')
        self.btn_save = JButton('Save')

        self.btn_cancel.setPreferredSize(Dimension(100, 32))
        self.btn_save.setPreferredSize(Dimension(100, 32))

        self.btn_cancel.addActionListener(lambda e: self._cancel_edit())
        self.btn_save.addActionListener(lambda e: self._save_sample())

        self.btn_cancel.setToolTipText("Cancel editing and clear form")
        self.btn_save.setToolTipText("Save sample to file")

        # Make Save button visually primary
        self.btn_save.setFont(self.btn_save.getFont().deriveFont(Font.BOLD))

        button_row.add(self.btn_cancel)
        button_row.add(self.btn_save)

        form_button_panel.add(button_row, BorderLayout.EAST)
        panel.add(form_button_panel, BorderLayout.SOUTH)

        return panel

    def _create_timeline_view(self):
        """Create timeline view panel with table"""
        panel = JPanel(BorderLayout())
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10))

        # Timeline table
        self.timeline_table_model = TimelineTableModel()
        self.timeline_table = JTable(self.timeline_table_model)
        self.timeline_table.setRowHeight(28)
        self.timeline_table.setShowGrid(True)
        self.timeline_table.setGridColor(Color(230, 230, 230))
        self.timeline_table.setAutoCreateRowSorter(True)

        # Configure columns
        col_model = self.timeline_table.getColumnModel()
        col_model.getColumn(0).setPreferredWidth(220)  # Date/Time
        col_model.getColumn(1).setPreferredWidth(180)  # Sample/Experiment
        col_model.getColumn(2).setPreferredWidth(250)  # Details

        # Custom renderer for highlighting
        self.timeline_table.setDefaultRenderer(Object, TimelineTableCellRenderer(self))

        # Double-click listener
        self.timeline_table.addMouseListener(TimelineMouseListener(self))

        scroll_pane = JScrollPane(self.timeline_table)
        panel.add(scroll_pane, BorderLayout.CENTER)

        return panel

    def _create_status_panel(self):
        """Create bottom status panel"""
        panel = JPanel(FlowLayout(FlowLayout.LEFT))
        panel.add(JLabel("Status:"))

        self.status_label = JLabel("Ready")
        panel.add(self.status_label)

        return panel

    def _navigate_to_curdata(self):
        """Navigate to current TopSpin dataset directory"""
        try:
            curdata = CURDATA()
            if curdata:
                # CURDATA returns [name, expno, procno, directory]
                # Full path is directory/name
                name = curdata[0]
                directory = curdata[3]
                full_path = os.path.join(directory, name)
                self.set_directory(full_path)
        except Exception as e:
            self.update_status("Could not navigate to CURDATA: %s" % str(e))

    def _browse_directory(self):
        """Browse for directory"""
        chooser = JFileChooser()
        chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)

        if self.current_directory:
            chooser.setCurrentDirectory(java.io.File(self.current_directory))

        result = chooser.showOpenDialog(self.frame)
        if result == JFileChooser.APPROVE_OPTION:
            selected_dir = chooser.getSelectedFile().getAbsolutePath()
            self.set_directory(selected_dir)

    def set_directory(self, directory):
        """Set current directory and refresh sample list"""
        self.current_directory = directory
        self.dir_label.setText(directory)
        self._refresh_sample_list()
        self._refresh_timeline()
        self.update_status("Directory: %s" % directory)

    def _refresh_sample_list(self):
        """Refresh the sample list from current directory"""
        if not self.current_directory:
            self.sample_table_model.clear_rows()
            return

        try:
            sample_files = self.sample_io.list_sample_files(self.current_directory)
            rows = []

            for filename in sample_files:
                filepath = os.path.join(self.current_directory, filename)
                status = self.sample_io.get_sample_status(filepath)

                # Load sample to get label and other info for tooltip
                try:
                    data = self.sample_io.read_sample(filepath)
                    label = data.get('Sample', {}).get('Label', filename)
                    created = data.get('Metadata', {}).get('created_timestamp', '')
                    users = data.get('Users', [])
                except:
                    label = filename
                    created = ''
                    users = []

                rows.append({
                    'status': status,
                    'label': label,
                    'filename': filename,
                    'created': created,
                    'users': users,
                    'filepath': filepath
                })

            self.sample_table_model.set_rows(rows)

        except Exception as e:
            self.update_status("Error refreshing sample list: %s" % str(e))

    def _get_schema_path_for_version(self, version):
        """Get schema path for a specific version"""
        # Try to load the specific version
        versioned_path = os.path.join(self.script_dir, 'schemas', 'v%s.json' % version)
        if os.path.exists(versioned_path):
            return versioned_path

        # Fall back to current schema if version not found
        return self.current_schema_path

    def _on_sample_selected(self):
        """Handle sample selection"""
        selected_row = self.sample_table.getSelectedRow()
        if selected_row < 0:
            self.btn_duplicate.setEnabled(False)
            self.btn_edit.setEnabled(False)
            self.selected_sample_filepath = None
            # Refresh timeline to clear highlighting
            self.timeline_table.repaint()
            return

        # Get row data
        row_data = self.sample_table_model.get_row(selected_row)
        filename = row_data['filename']
        self.current_sample_file = filename
        self.selected_sample_filepath = row_data['filepath']

        # Enable buttons
        self.btn_duplicate.setEnabled(True)
        self.btn_edit.setEnabled(True)

        # Load sample data into form
        self._load_sample_into_form(filename)

        # Refresh timeline to highlight this sample's events
        self.timeline_table.repaint()

    def _load_sample_into_form(self, filename):
        """Load sample data into form"""
        if not self.current_directory:
            return

        try:
            filepath = os.path.join(self.current_directory, filename)
            data = self.sample_io.read_sample(filepath)

            # Determine which schema to use for editing
            schema_version = data.get('Metadata', {}).get('schema_version', '0.0.1')
            schema_path = self._get_schema_path_for_version(schema_version)

            # Always create a fresh form generator to avoid stale component references
            self.form_generator = SchemaFormGenerator(schema_path)

            # Create form panel first
            self.form_panel.removeAll()
            form_scroll = self.form_generator.create_form_panel(self)  # Pass app for modification tracking
            self.form_panel.add(form_scroll, BorderLayout.CENTER)

            # THEN load data into the now-created components
            self.form_generator.load_data(data)

            self.form_panel.revalidate()
            self.form_panel.repaint()

            # Reset modification flag and disable buttons
            self.form_modified = False
            self.btn_save.setEnabled(False)
            self.btn_cancel.setEnabled(False)

            self.update_status("Loaded sample: %s (schema v%s)" % (filename, schema_version))

        except Exception as e:
            self.update_status("Error loading sample: %s" % str(e))

    def _new_sample(self):
        """Create new sample"""
        # Auto-eject any active sample
        try:
            ejected = self.sample_io.auto_eject_active_sample(self.current_directory)
            if ejected:
                self.update_status("Auto-ejected active sample: %s" % ejected)
        except Exception as e:
            self.update_status("Warning: Could not auto-eject: %s" % str(e))

        # Create fresh form generator using CURRENT schema for new samples
        self.form_generator = SchemaFormGenerator(self.current_schema_path)

        # Create empty form
        self.form_panel.removeAll()
        form_scroll = self.form_generator.create_form_panel(self)  # Pass app for modification tracking
        self.form_panel.add(form_scroll, BorderLayout.CENTER)
        self.form_panel.revalidate()
        self.form_panel.repaint()

        self.current_sample_file = None
        self.form_modified = False
        self.btn_save.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.tabbed_pane.setSelectedIndex(0)  # Switch to Sample Details tab
        self.update_status("Creating new sample")

    def _duplicate_sample(self):
        """Duplicate selected sample"""
        if not self.current_sample_file:
            self.update_status("Please select a sample to duplicate")
            return

        try:
            filepath = os.path.join(self.current_directory, self.current_sample_file)
            data = self.sample_io.read_sample(filepath)

            # Remove metadata timestamps - will be regenerated with current schema
            if 'Metadata' in data:
                data['Metadata'].pop('created_timestamp', None)
                data['Metadata'].pop('modified_timestamp', None)
                data['Metadata'].pop('ejected_timestamp', None)
                data['Metadata'].pop('schema_version', None)

            # Create fresh form generator using CURRENT schema for duplicates
            self.form_generator = SchemaFormGenerator(self.current_schema_path)

            # Create form first
            self.form_panel.removeAll()
            form_scroll = self.form_generator.create_form_panel(self)  # Pass app for modification tracking
            self.form_panel.add(form_scroll, BorderLayout.CENTER)

            # Then load data
            self.form_generator.load_data(data)

            self.form_panel.revalidate()
            self.form_panel.repaint()

            self.current_sample_file = None
            self.form_modified = False
            self.btn_save.setEnabled(False)
            self.btn_cancel.setEnabled(False)
            self.tabbed_pane.setSelectedIndex(0)  # Switch to Sample Details tab
            self.update_status("Duplicating sample")

        except Exception as e:
            self.update_status("Error duplicating sample: %s" % str(e))

    def _edit_sample(self):
        """Edit selected sample"""
        if not self.current_sample_file:
            MSG("Please select a sample to edit")
            return

        self._load_sample_into_form(self.current_sample_file)
        self.tabbed_pane.setSelectedIndex(0)  # Switch to Sample Details tab

    def _eject_sample(self):
        """Eject selected sample (virtual - timestamp only)"""
        if not self.current_sample_file:
            MSG("Please select a sample to eject")
            return

        try:
            filepath = os.path.join(self.current_directory, self.current_sample_file)
            self.sample_io.eject_sample(filepath)
            self._refresh_sample_list()
            self.update_status("Ejected sample: %s" % self.current_sample_file)
        except Exception as e:
            MSG("Error ejecting sample: %s" % str(e))

    def _eject_sample_physical(self):
        """Eject sample physically and virtually"""
        self._eject_sample()
        # TODO: Call TopSpin physical eject command
        MSG("Physical eject: Please eject sample from spectrometer")

    def _save_sample(self):
        """Save current form data"""
        if not self.current_directory:
            MSG("No directory selected")
            return

        if not self.form_generator:
            MSG("No form data to save")
            return

        try:
            # Get data from form
            data = self.form_generator.get_data()

            # Generate filename if new sample
            if not self.current_sample_file:
                sample_label = data.get('Sample', {}).get('Label', 'Sample')
                filename = self.sample_io.generate_filename(sample_label)
                is_new = True
            else:
                filename = self.current_sample_file
                is_new = False

                # When editing existing sample, preserve existing metadata
                filepath = os.path.join(self.current_directory, filename)
                try:
                    existing_data = self.sample_io.read_sample(filepath)
                    # Preserve metadata fields that shouldn't be changed by editing
                    if 'Metadata' in existing_data:
                        if 'Metadata' not in data:
                            data['Metadata'] = {}
                        # Preserve creation timestamp and ejection timestamp
                        data['Metadata']['created_timestamp'] = existing_data['Metadata'].get('created_timestamp')
                        if 'ejected_timestamp' in existing_data['Metadata']:
                            data['Metadata']['ejected_timestamp'] = existing_data['Metadata'].get('ejected_timestamp')
                except:
                    pass  # If we can't read existing, proceed without preserved metadata

            filepath = os.path.join(self.current_directory, filename)

            # Write sample
            self.sample_io.write_sample(filepath, data, is_new=is_new)

            self._refresh_sample_list()

            # Reset modification flag and disable buttons
            self.form_modified = False
            self.btn_save.setEnabled(False)
            self.btn_cancel.setEnabled(False)

            self.update_status("Saved sample: %s" % filename)

        except Exception as e:
            MSG("Error saving sample: %s" % str(e))

    def _cancel_edit(self):
        """Cancel current edit"""
        # If form was modified, confirm cancellation
        if self.form_modified:
            result = JOptionPane.showConfirmDialog(
                self.frame,
                "You have unsaved changes. Discard them?",
                "Discard Changes",
                JOptionPane.YES_NO_OPTION,
                JOptionPane.WARNING_MESSAGE
            )
            if result != JOptionPane.YES_OPTION:  # User clicked No or closed dialog
                return

        self.current_sample_file = None
        self.form_modified = False
        self.btn_save.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.form_panel.removeAll()
        placeholder = JLabel("Select a sample or create a new one", JLabel.CENTER)
        self.form_panel.add(placeholder, BorderLayout.CENTER)
        self.form_panel.revalidate()
        self.form_panel.repaint()
        self.update_status("Cancelled")

    def _refresh_timeline(self):
        """Refresh timeline view"""
        if not self.current_directory:
            self.timeline_table_model.clear_rows()
            return

        try:
            entries = self.timeline_builder.build_timeline(self.current_directory)
            rows = []
            current_sample_filepath = None
            current_sample_color_index = 0  # Track color index for alternating

            for entry in entries:
                # Format timestamp for display - capitalize, no zero padding
                # Manual formatting for cross-platform compatibility
                day_name = entry.timestamp.strftime("%a")  # Mon, Tue, etc.
                day = entry.timestamp.day  # 1-31, no zero padding
                month = entry.timestamp.strftime("%b")  # Jan, Feb, etc.
                year = entry.timestamp.year
                hour = entry.timestamp.hour
                minute = entry.timestamp.minute

                # Convert to 12-hour format
                if hour == 0:
                    hour_12 = 12
                    am_pm = "AM"
                elif hour < 12:
                    hour_12 = hour
                    am_pm = "AM"
                elif hour == 12:
                    hour_12 = 12
                    am_pm = "PM"
                else:
                    hour_12 = hour - 12
                    am_pm = "PM"

                timestamp_str = "%s %d %s %d, %d.%02d %s" % (day_name, day, month, year, hour_12, minute, am_pm)

                # Determine display name and track sample changes
                if entry.entry_type == 'sample_created':
                    display_name = entry.name
                    # New sample - toggle color
                    if current_sample_filepath != entry.filepath:
                        current_sample_color_index = 1 - current_sample_color_index
                    current_sample_filepath = entry.filepath
                elif entry.entry_type == 'sample_ejected':
                    display_name = "sample ejected"
                    # Keep current_sample_filepath and color for coloring
                elif entry.entry_type == 'experiment':
                    display_name = "Exp %s" % entry.name
                else:
                    display_name = entry.name

                # Extract just pulse program name from details (no nuclei, no scans)
                details = entry.details
                if details and ',' in details:
                    details = details.split(',')[0].strip()  # Just the pulse program

                rows.append({
                    'timestamp': timestamp_str,
                    'name': display_name,
                    'details': details,
                    'entry': entry,
                    'sample_filepath': current_sample_filepath,  # For highlighting
                    'color_index': current_sample_color_index  # For consistent coloring
                })

            self.timeline_table_model.set_rows(rows)

        except Exception as e:
            self.update_status("Error refreshing timeline: %s" % str(e))

    def handle_timeline_double_click(self, selected_entry):
        """Handle double-click on timeline entry"""
        if selected_entry.entry_type == 'experiment' and selected_entry.filepath:
            # Open experiment in TopSpin
            try:
                # Parse directory to get dataset info
                # filepath is like: /path/to/datadir/expname/expno
                expno_dir = selected_entry.filepath
                expname_dir = os.path.dirname(expno_dir)  # /path/to/datadir/expname
                data_dir = os.path.dirname(expname_dir)  # /path/to/datadir
                expname = os.path.basename(expname_dir)  # experiment name (folder)
                expno = selected_entry.name  # experiment number as string
                procno = "1"  # Always use procno 1

                # RE() must be run in a command thread via EXEC_PYSCRIPT
                # Format the command as a single-line string
                cmd = 'RE(["%s", "%s", "%s", "%s"])' % (expname, expno, procno, data_dir)
                EXEC_PYSCRIPT(cmd)
                self.update_status("Opening experiment %s/%s" % (expname, expno))

            except Exception as e:
                self.update_status("Error opening experiment: %s" % str(e))

    def update_status(self, text):
        """Update status label"""
        self.status_label.setText(text)

    def show(self):
        """Show the window if hidden"""
        if self.frame is not None:
            self.frame.setVisible(True)
            self.frame.toFront()
            self.frame.requestFocus()

    def shutdown(self):
        """Properly shut down the application"""
        # Remove from system properties first
        System.getProperties().remove(APP_KEY)

        # Then dispose the frame
        if self.frame is not None:
            self.frame.dispose()


class SampleTableModel(AbstractTableModel):
    """Table model for sample list"""

    def __init__(self):
        self.rows = []
        self.column_names = ['', 'Sample']

    def getColumnCount(self):
        return len(self.column_names)

    def getRowCount(self):
        return len(self.rows)

    def getColumnName(self, col):
        return self.column_names[col]

    def getValueAt(self, row, col):
        if row >= len(self.rows):
            return None
        row_data = self.rows[row]
        if col == 0:
            return row_data['status']
        elif col == 1:
            return row_data['label']
        return None

    def get_row(self, row):
        """Get full row data"""
        if row >= 0 and row < len(self.rows):
            return self.rows[row]
        return None

    def set_rows(self, rows):
        """Replace all rows"""
        self.rows = rows
        self.fireTableDataChanged()

    def clear_rows(self):
        """Clear all rows"""
        self.rows = []
        self.fireTableDataChanged()


class SampleTableCellRenderer(DefaultTableCellRenderer):
    """Custom cell renderer for sample table with status icons"""

    def getTableCellRendererComponent(self, table, value, isSelected, hasFocus, row, column):
        component = DefaultTableCellRenderer.getTableCellRendererComponent(
            self, table, value, isSelected, hasFocus, row, column)

        # Get row data for tooltip and icon
        model = table.getModel()
        row_data = model.get_row(row)

        if row_data:
            # Set tooltip with detailed info
            filename = row_data.get('filename', '')
            created = row_data.get('created', '')
            users = row_data.get('users', [])
            users_str = ', '.join(users) if users else 'None'

            tooltip = "<html><b>File:</b> %s<br><b>Created:</b> %s<br><b>Users:</b> %s</html>" % (
                filename, created[:19] if created else 'Unknown', users_str)
            component.setToolTipText(tooltip)

            # Column 0: Status icon
            if column == 0:
                status = row_data.get('status', 'unknown')
                if status == 'loaded':
                    component.setText(u"\u25CF")  # Filled circle
                    component.setForeground(Color(34, 139, 34))  # Forest green
                elif status == 'ejected':
                    component.setText(u"\u25CF")  # Filled circle
                    component.setForeground(Color(128, 128, 128))  # Grey
                else:
                    component.setText(u"\u25CB")  # Hollow circle
                    component.setForeground(Color(128, 128, 128))
                component.setHorizontalAlignment(JLabel.CENTER)
            # Column 1: Sample label
            elif column == 1:
                component.setHorizontalAlignment(JLabel.LEFT)
                if not isSelected:
                    component.setForeground(Color.BLACK)

        return component


class TimelineTableModel(AbstractTableModel):
    """Table model for timeline"""

    def __init__(self):
        self.rows = []
        self.column_names = ['Date/Time', 'Sample/Experiment', 'Details']

    def getColumnCount(self):
        return len(self.column_names)

    def getRowCount(self):
        return len(self.rows)

    def getColumnName(self, col):
        return self.column_names[col]

    def getValueAt(self, row, col):
        if row >= len(self.rows):
            return None
        row_data = self.rows[row]
        if col == 0:
            return row_data['timestamp']
        elif col == 1:
            return row_data['name']
        elif col == 2:
            return row_data['details']
        return None

    def get_row(self, row):
        """Get full row data"""
        if row >= 0 and row < len(self.rows):
            return self.rows[row]
        return None

    def set_rows(self, rows):
        """Replace all rows"""
        self.rows = rows
        self.fireTableDataChanged()

    def clear_rows(self):
        """Clear all rows"""
        self.rows = []
        self.fireTableDataChanged()


class TimelineTableCellRenderer(DefaultTableCellRenderer):
    """Custom cell renderer for timeline table with sample highlighting"""

    def __init__(self, app):
        DefaultTableCellRenderer.__init__(self)
        self.app = app
        # Simple two-color alternation
        self.color_white = Color.WHITE
        self.color_grey = Color(245, 245, 245)

    def getTableCellRendererComponent(self, table, value, isSelected, hasFocus, row, column):
        component = DefaultTableCellRenderer.getTableCellRendererComponent(
            self, table, value, isSelected, hasFocus, row, column)

        # Get row data
        model = table.getModel()
        row_data = model.get_row(row)

        if row_data and not isSelected:
            sample_filepath = row_data.get('sample_filepath')
            color_index = row_data.get('color_index', 0)

            # Highlight rows matching selected sample (softer yellow)
            if self.app.selected_sample_filepath and sample_filepath == self.app.selected_sample_filepath:
                component.setBackground(Color(255, 252, 230))  # Soft pale yellow
            else:
                # Alternate colors by sample using color_index
                if color_index == 0:
                    component.setBackground(self.color_white)
                else:
                    component.setBackground(self.color_grey)

        # Color pulse programs by dimensionality in Details column
        if column == 2 and value and not isSelected:
            pulprog = str(value).strip()

            # Determine dimensionality and color
            if pulprog:
                # 3D+ experiments (green)
                if any(x in pulprog.lower() for x in ['3d', 'hncacb', 'hnco', 'hnca', 'hncaco', 'cbcaconh']):
                    component.setForeground(Color(0, 128, 0))  # Green
                # 2D experiments (blue)
                elif any(x in pulprog.lower() for x in ['2d', 'hsqc', 'hmqc', 'hmbc', 'cosy', 'tocsy', 'noesy', 'roesy']):
                    component.setForeground(Color(0, 0, 200))  # Blue
                # 1D experiments (black) - default
                else:
                    component.setForeground(Color.BLACK)
            else:
                component.setForeground(Color.BLACK)
        elif not isSelected:
            component.setForeground(Color.BLACK)

        return component


class SampleTableMouseListener(MouseAdapter):
    """Mouse listener for sample table (right-click context menu)"""

    def __init__(self, app):
        self.app = app

    def mousePressed(self, event):
        self._handle_popup(event)

    def mouseReleased(self, event):
        self._handle_popup(event)

    def _handle_popup(self, event):
        if event.isPopupTrigger():
            table = event.getSource()
            row = table.rowAtPoint(event.getPoint())

            # Select row if not already selected
            if row >= 0 and row != table.getSelectedRow():
                table.setRowSelectionInterval(row, row)

            # Create context menu
            popup = JPopupMenu()

            item_new = JMenuItem("New Sample")
            item_new.addActionListener(lambda e: self.app._new_sample())
            popup.add(item_new)

            if row >= 0:
                popup.addSeparator()

                item_duplicate = JMenuItem("Duplicate")
                item_duplicate.addActionListener(lambda e: self.app._duplicate_sample())
                popup.add(item_duplicate)

                item_edit = JMenuItem("Edit")
                item_edit.addActionListener(lambda e: self.app._edit_sample())
                popup.add(item_edit)

                popup.addSeparator()

                item_eject = JMenuItem("Eject (Virtual)")
                item_eject.addActionListener(lambda e: self.app._eject_sample())
                popup.add(item_eject)

                item_eject_phys = JMenuItem("Eject (Physical)")
                item_eject_phys.addActionListener(lambda e: self.app._eject_sample_physical())
                popup.add(item_eject_phys)

                # TODO: Add delete option in future

            popup.show(event.getComponent(), event.getX(), event.getY())


class TimelineMouseListener(MouseAdapter):
    """Mouse listener for timeline double-clicks"""

    def __init__(self, app):
        self.app = app

    def mouseClicked(self, event):
        if event.getClickCount() == 2:
            table = event.getSource()
            row = table.rowAtPoint(event.getPoint())
            if row >= 0:
                row_data = table.getModel().get_row(row)
                if row_data and 'entry' in row_data:
                    self.app.handle_timeline_double_click(row_data['entry'])


class CancelAction(AbstractAction):
    """Action to handle Escape key for cancelling form edits"""

    def __init__(self, app):
        AbstractAction.__init__(self)
        self.app = app

    def actionPerformed(self, event):
        self.app._cancel_edit()


def get_app():
    """Get or create the application singleton"""
    app = System.getProperties().get(APP_KEY)

    if app is None:
        # No existing app - reload modules to get fresh code
        try:
            import sample_io
            import schema_form
            import timeline
            reload(sample_io)
            reload(schema_form)
            reload(timeline)
        except:
            pass

        # Create new instance
        app = SampleManagerApp()
        System.getProperties().put(APP_KEY, app)
    else:
        # Version check for code updates
        if not hasattr(app, 'show'):
            # Old version - replace it
            try:
                import sample_io
                import schema_form
                import timeline
                reload(sample_io)
                reload(schema_form)
                reload(timeline)
            except:
                pass
            app = SampleManagerApp()
            System.getProperties().put(APP_KEY, app)
        else:
            # Show existing instance
            app.show()

    return app


def main():
    get_app()


# Run main
main()
