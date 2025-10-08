# -*- coding: utf-8 -*-
"""
NMR Sample Manager - Main GUI Application
Persistent Jython/Swing application for managing NMR sample metadata in TopSpin
"""

from javax.swing import *
from javax.swing import DefaultListCellRenderer
from java.awt import *
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

        self.schema_path = os.path.join(script_dir, 'schemas', 'current.json')
        self.form_generator = None
        self.current_sample_file = None
        self.timeline_builder = TimelineBuilder(self.sample_io)

        # GUI components
        self.frame = None
        self.status_label = None
        self.dir_label = None
        self.sample_list = None
        self.sample_list_model = None
        self.form_panel = None
        self.timeline_list = None
        self.timeline_model = None
        self.card_layout = None
        self.main_panel = None

        # Initialize
        self._create_gui()
        self._navigate_to_curdata()

    def _create_gui(self):
        """Build the GUI"""
        self.frame = JFrame('NMR Sample Manager')
        self.frame.setSize(900, 700)
        self.frame.setDefaultCloseOperation(WindowConstants.HIDE_ON_CLOSE)

        # Main container
        container = self.frame.getContentPane()
        container.setLayout(BorderLayout())

        # Top panel - directory info and navigation
        top_panel = self._create_top_panel()
        container.add(top_panel, BorderLayout.NORTH)

        # Center panel - card layout for form/timeline views
        self.card_layout = CardLayout()
        self.main_panel = JPanel(self.card_layout)

        # Left-right split
        split_pane = JSplitPane(JSplitPane.HORIZONTAL_SPLIT)
        split_pane.setDividerLocation(250)

        # Left - sample list
        list_panel = self._create_sample_list_panel()
        split_pane.setLeftComponent(list_panel)

        # Right - form view and timeline view (card layout)
        form_view = self._create_form_view()
        timeline_view = self._create_timeline_view()

        self.main_panel.add(form_view, "form")
        self.main_panel.add(timeline_view, "timeline")

        split_pane.setRightComponent(self.main_panel)
        container.add(split_pane, BorderLayout.CENTER)

        # Bottom panel - status bar
        status_panel = self._create_status_panel()
        container.add(status_panel, BorderLayout.SOUTH)

        self.frame.setVisible(True)

    def _create_top_panel(self):
        """Create top panel with directory navigation"""
        panel = JPanel(FlowLayout(FlowLayout.LEFT))

        panel.add(JLabel("Current Directory:"))

        self.dir_label = JLabel("None")
        panel.add(self.dir_label)

        btn_browse = JButton('Browse...', actionPerformed=lambda e: self._browse_directory())
        panel.add(btn_browse)

        btn_timeline = JButton('Show Timeline', actionPerformed=lambda e: self._show_timeline())
        panel.add(btn_timeline)

        btn_form = JButton('Show Form', actionPerformed=lambda e: self._show_form())
        panel.add(btn_form)

        return panel

    def _create_sample_list_panel(self):
        """Create left panel with sample list and action buttons"""
        panel = JPanel(BorderLayout())
        panel.setBorder(BorderFactory.createTitledBorder("Samples"))

        # Sample list
        self.sample_list_model = DefaultListModel()
        self.sample_list = JList(self.sample_list_model)
        self.sample_list.setSelectionMode(ListSelectionModel.SINGLE_SELECTION)
        self.sample_list.addListSelectionListener(lambda e: self._on_sample_selected() if not e.getValueIsAdjusting() else None)

        scroll_pane = JScrollPane(self.sample_list)
        panel.add(scroll_pane, BorderLayout.CENTER)

        # Button panel
        button_panel = JPanel()
        button_panel.setLayout(GridLayout(0, 1, 5, 5))

        btn_new = JButton('New Sample', actionPerformed=lambda e: self._new_sample())
        btn_duplicate = JButton('Duplicate', actionPerformed=lambda e: self._duplicate_sample())
        btn_edit = JButton('Edit', actionPerformed=lambda e: self._edit_sample())
        btn_eject = JButton('Eject (Virtual)', actionPerformed=lambda e: self._eject_sample())
        btn_eject_physical = JButton('Eject (Physical)', actionPerformed=lambda e: self._eject_sample_physical())

        button_panel.add(btn_new)
        button_panel.add(btn_duplicate)
        button_panel.add(btn_edit)
        button_panel.add(btn_eject)
        button_panel.add(btn_eject_physical)

        panel.add(button_panel, BorderLayout.SOUTH)

        return panel

    def _create_form_view(self):
        """Create form view panel"""
        panel = JPanel(BorderLayout())

        # Placeholder for form
        self.form_panel = JPanel()
        self.form_panel.setLayout(BorderLayout())
        placeholder = JLabel("Select a sample or create a new one", JLabel.CENTER)
        self.form_panel.add(placeholder, BorderLayout.CENTER)

        # Button panel for form actions
        form_buttons = JPanel(FlowLayout(FlowLayout.RIGHT))
        btn_save = JButton('Save', actionPerformed=lambda e: self._save_sample())
        btn_cancel = JButton('Cancel', actionPerformed=lambda e: self._cancel_edit())
        form_buttons.add(btn_save)
        form_buttons.add(btn_cancel)

        panel.add(self.form_panel, BorderLayout.CENTER)
        panel.add(form_buttons, BorderLayout.SOUTH)

        return panel

    def _create_timeline_view(self):
        """Create timeline view panel"""
        panel = JPanel(BorderLayout())
        panel.setBorder(BorderFactory.createTitledBorder("Timeline"))

        # Timeline list with custom renderer
        self.timeline_model = DefaultListModel()
        self.timeline_list = JList(self.timeline_model)

        # Use custom cell renderer to display TimelineEntry objects
        self.timeline_list.setCellRenderer(TimelineListCellRenderer())
        self.timeline_list.addMouseListener(TimelineMouseListener(self))

        scroll_pane = JScrollPane(self.timeline_list)
        panel.add(scroll_pane, BorderLayout.CENTER)

        return panel

    def _create_status_panel(self):
        """Create bottom status panel"""
        panel = JPanel(FlowLayout(FlowLayout.LEFT))
        panel.add(JLabel("Status:"))

        self.status_label = JLabel("Ready")
        panel.add(self.status_label)

        # Add Quit button
        btn_quit = JButton('Quit', actionPerformed=lambda e: self.shutdown())
        panel.add(btn_quit)

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
        self.update_status("Directory: %s" % directory)

    def _refresh_sample_list(self):
        """Refresh the sample list from current directory"""
        self.sample_list_model.clear()

        if not self.current_directory:
            return

        try:
            sample_files = self.sample_io.list_sample_files(self.current_directory)

            for filename in sample_files:
                filepath = os.path.join(self.current_directory, filename)
                status = self.sample_io.get_sample_status(filepath)
                display_name = "%s [%s]" % (filename, status.upper())
                self.sample_list_model.addElement(display_name)

        except Exception as e:
            self.update_status("Error refreshing sample list: %s" % str(e))

    def _on_sample_selected(self):
        """Handle sample selection"""
        selected = self.sample_list.getSelectedValue()
        if not selected:
            return

        # Extract filename from display name
        filename = selected.split(' [')[0]
        self.current_sample_file = filename

        # Load sample data into form
        self._load_sample_into_form(filename)

    def _load_sample_into_form(self, filename):
        """Load sample data into form"""
        if not self.current_directory:
            return

        try:
            filepath = os.path.join(self.current_directory, filename)
            data = self.sample_io.read_sample(filepath)

            # Always create a fresh form generator to avoid stale component references
            self.form_generator = SchemaFormGenerator(self.schema_path)

            # Create form panel first
            self.form_panel.removeAll()
            form_scroll = self.form_generator.create_form_panel()
            self.form_panel.add(form_scroll, BorderLayout.CENTER)

            # THEN load data into the now-created components
            self.form_generator.load_data(data)

            self.form_panel.revalidate()
            self.form_panel.repaint()

            self.update_status("Loaded sample: %s" % filename)

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

        # Create fresh form generator
        self.form_generator = SchemaFormGenerator(self.schema_path)

        # Create empty form
        self.form_panel.removeAll()
        form_scroll = self.form_generator.create_form_panel()
        self.form_panel.add(form_scroll, BorderLayout.CENTER)
        self.form_panel.revalidate()
        self.form_panel.repaint()

        self.current_sample_file = None
        self.card_layout.show(self.main_panel, "form")
        self.update_status("Creating new sample")

    def _duplicate_sample(self):
        """Duplicate selected sample"""
        if not self.current_sample_file:
            self.update_status("Please select a sample to duplicate")
            return

        try:
            filepath = os.path.join(self.current_directory, self.current_sample_file)
            data = self.sample_io.read_sample(filepath)

            # Remove metadata timestamps
            if 'Metadata' in data:
                data['Metadata'].pop('created_timestamp', None)
                data['Metadata'].pop('modified_timestamp', None)
                data['Metadata'].pop('ejected_timestamp', None)

            # Create fresh form generator
            self.form_generator = SchemaFormGenerator(self.schema_path)

            # Create form first
            self.form_panel.removeAll()
            form_scroll = self.form_generator.create_form_panel()
            self.form_panel.add(form_scroll, BorderLayout.CENTER)

            # Then load data
            self.form_generator.load_data(data)

            self.form_panel.revalidate()
            self.form_panel.repaint()

            self.current_sample_file = None
            self.card_layout.show(self.main_panel, "form")
            self.update_status("Duplicating sample")

        except Exception as e:
            self.update_status("Error duplicating sample: %s" % str(e))

    def _edit_sample(self):
        """Edit selected sample"""
        if not self.current_sample_file:
            MSG("Please select a sample to edit")
            return

        self._load_sample_into_form(self.current_sample_file)
        self.card_layout.show(self.main_panel, "form")

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

            filepath = os.path.join(self.current_directory, filename)

            # Write sample
            self.sample_io.write_sample(filepath, data, is_new=is_new)

            self._refresh_sample_list()
            self.update_status("Saved sample: %s" % filename)

        except Exception as e:
            MSG("Error saving sample: %s" % str(e))

    def _cancel_edit(self):
        """Cancel current edit"""
        self.current_sample_file = None
        self.form_panel.removeAll()
        placeholder = JLabel("Select a sample or create a new one", JLabel.CENTER)
        self.form_panel.add(placeholder, BorderLayout.CENTER)
        self.form_panel.revalidate()
        self.form_panel.repaint()
        self.update_status("Cancelled")

    def _show_timeline(self):
        """Show timeline view"""
        self.card_layout.show(self.main_panel, "timeline")
        self._refresh_timeline()

    def _show_form(self):
        """Show form view"""
        self.card_layout.show(self.main_panel, "form")

    def _refresh_timeline(self):
        """Refresh timeline view"""
        self.timeline_model.clear()

        if not self.current_directory:
            return

        try:
            entries = self.timeline_builder.build_timeline(self.current_directory)

            for entry in entries:
                self.timeline_model.addElement(entry)

            self.update_status("Timeline refreshed")

        except Exception as e:
            self.update_status("Error refreshing timeline: %s" % str(e))

    def handle_timeline_double_click(self, selected_entry):
        """Handle double-click on timeline entry"""
        if selected_entry.entry_type == 'experiment' and selected_entry.filepath:
            # Open experiment in TopSpin
            try:
                # Parse directory to get dataset info
                # filepath is like: /path/to/dataset/name/expno
                expno_dir = selected_entry.filepath
                parent_dir = os.path.dirname(expno_dir)  # /path/to/dataset/name
                grandparent_dir = os.path.dirname(parent_dir)  # /path/to/dataset
                name = os.path.basename(parent_dir)
                expno = int(selected_entry.name)
                procno = 1  # Default to procno 1

                # Use RE() to open the experiment
                RE([name, expno, procno, grandparent_dir])
                self.update_status("Opened experiment %s/%d" % (name, expno))

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


class TimelineListCellRenderer(DefaultListCellRenderer):
    """Custom cell renderer for timeline entries"""

    def getListCellRendererComponent(self, list, value, index, isSelected, cellHasFocus):
        # Get the default component
        component = DefaultListCellRenderer.getListCellRendererComponent(
            self, list, value, index, isSelected, cellHasFocus)

        # If value is a TimelineEntry, get its display text
        if hasattr(value, 'get_display_text'):
            component.setText(value.get_display_text())
        else:
            component.setText(str(value))

        return component


class TimelineMouseListener(java.awt.event.MouseAdapter):
    """Mouse listener for timeline double-clicks"""

    def __init__(self, app):
        self.app = app

    def mouseClicked(self, event):
        if event.getClickCount() == 2:
            list_component = event.getSource()
            index = list_component.locationToIndex(event.getPoint())
            if index >= 0:
                selected_entry = list_component.getModel().getElementAt(index)
                self.app.handle_timeline_double_click(selected_entry)


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
