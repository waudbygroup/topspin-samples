# -*- coding: utf-8 -*-
"""
NMR Sample Manager - Main GUI Application
Persistent Jython/Swing application for managing NMR sample metadata in TopSpin
"""

from javax.swing import *
from javax.swing.event import DocumentListener
from javax.swing.table import DefaultTableModel, AbstractTableModel, DefaultTableCellRenderer
from java.awt import *
from java.awt.event import MouseAdapter, KeyEvent
from javax.swing import AbstractAction, KeyStroke, JComponent, DefaultListModel
from java.lang import System
import java.awt.event
import sys
import os
import json
from datetime import datetime, timedelta

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
from config_manager import ConfigManager
from sample_scanner import SampleScanner
from html_view import HTMLViewGenerator

APP_KEY = "org.nmr-samples.topspin"


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
        self.current_schema_path = os.path.join(script_dir, 'schemas', 'current', 'schema.json')
        self.form_generator = None
        self.current_sample_file = None
        self.timeline_builder = TimelineBuilder(self.sample_io)
        self.form_modified = False  # Track if form has been edited
        self.is_draft = False  # Track if current form is an unsaved draft
        self.draft_data = None  # Store draft data for unsaved samples

        # Configuration manager
        config_file = os.path.join(script_dir, 'config.json')
        self.config = ConfigManager(config_file)

        # Sample scanner
        self.sample_scanner = SampleScanner(self.sample_io)

        # GUI components
        self.frame = None
        self.status_label = None
        self.update_label = None
        self.dir_label = None
        self.sample_table = None
        self.sample_table_model = None
        self.btn_new = None
        self.btn_duplicate = None
        self.btn_edit = None
        self.btn_eject = None
        self.btn_delete = None
        self.btn_save = None
        self.btn_cancel = None
        self.form_panel = None
        self.timeline_table = None
        self.timeline_table_model = None
        self.create_from_selection_btn = None
        self.reassign_prev_btn = None
        self.reassign_next_btn = None
        self.view_sample_btn = None
        self.open_experiment_btn = None
        self.tabbed_pane = None
        self.selected_sample_filepath = None
        self.badge_label = None
        self.badge_detail_label = None
        self.catalogue_table = None
        self.catalogue_table_model = None
        self.catalogue_search_field = None
        self.catalogue_btn_view = None
        self.catalogue_btn_edit = None
        self.catalogue_btn_duplicate = None
        self.catalogue_center_panel = None  # CardLayout panel for table/empty state

        # Initialize
        self._create_gui()
        self._set_initial_button_states()
        self._navigate_to_curdata()
        # Check for updates in background
        self._check_updates_background()

    def _set_initial_button_states(self):
        """Set initial button enabled/disabled states"""
        self.btn_duplicate.setEnabled(False)
        self.btn_edit.setEnabled(False)
        self.btn_eject.setEnabled(False)
        self.btn_delete.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.btn_cancel.setEnabled(False)

        # Set initial button visibility - hide Save/Cancel initially, disable Edit
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_edit.setEnabled(False)

    def mark_form_modified(self):
        """Mark form as modified and enable Save/Cancel buttons"""
        self.form_modified = True
        self.btn_save.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        # Update draft data for badge display
        if self.is_draft and self.form_generator:
            self.draft_data = self.form_generator.get_data()
            self._update_badge()

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

    def _check_for_updates(self):
        """Check if git updates are available

        Returns:
            tuple: (has_updates, error_message, debug_info) where has_updates is bool or None if error
        """
        try:
            import subprocess

            # First, try to fetch from remote (silently)
            self.update_status("Checking for updates - fetching...")
            try:
                subprocess.check_output(
                    ['git', 'fetch', 'origin'],
                    cwd=self.script_dir,
                    stderr=subprocess.STDOUT
                )
            except subprocess.CalledProcessError as e:
                # Fetch failed - might be offline or no git
                debug_msg = "Fetch failed: %s" % str(e)
                self.update_status("Ready")
                return (None, "Unable to check for updates - check internet connection", debug_msg)
            except Exception as e:
                # Other error (timeout, git not available, etc.)
                debug_msg = "Fetch error: %s" % str(e)
                self.update_status("Ready")
                return (None, "Unable to check for updates", debug_msg)

            # Compare local HEAD with origin/main
            self.update_status("Checking for updates - comparing versions...")
            try:
                local = subprocess.check_output(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=self.script_dir,
                    stderr=subprocess.STDOUT
                ).strip()

                remote = subprocess.check_output(
                    ['git', 'rev-parse', 'origin/main'],
                    cwd=self.script_dir,
                    stderr=subprocess.STDOUT
                ).strip()

                # Check if we're behind
                if local != remote:
                    # Check if local is ancestor of remote (we're behind)
                    try:
                        subprocess.check_output(
                            ['git', 'merge-base', '--is-ancestor', 'HEAD', 'origin/main'],
                            cwd=self.script_dir,
                            stderr=subprocess.STDOUT
                        )
                        debug_msg = "Checked for updates - local version: %s, remote version: %s" % (local[:8], remote[:8])
                        self.update_status(debug_msg)
                        return (True, None, debug_msg)  # Updates available
                    except subprocess.CalledProcessError:
                        # We have diverged - not a simple update case
                        debug_msg = "Checked for updates - local version: %s, remote version: %s (diverged)" % (local[:8], remote[:8])
                        self.update_status(debug_msg)
                        return (None, "Local changes detected", debug_msg)

                debug_msg = "Checked for updates - up to date (version: %s)" % local[:8]
                self.update_status(debug_msg)
                return (False, None, debug_msg)  # Up to date

            except Exception as e:
                debug_msg = "Version compare error: %s" % str(e)
                self.update_status("Ready")
                return (None, "Unable to compare versions", debug_msg)

        except Exception as e:
            # Git not available or other error
            debug_msg = "Git error: %s" % str(e)
            self.update_status("Ready")
            return (None, None, debug_msg)

    def _create_gui(self):
        """Build the GUI"""
        # Get git version for window title
        git_version = self._get_git_version()
        title = "NMR Sample Manager"
        if git_version:
            title = "%s (version ref: %s)" % (title, git_version)

        self.frame = JFrame(title)
        self.frame.setSize(1200, 700)
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

        # Right - tabbed pane with Sample Details, Timeline, and Samples
        self.tabbed_pane = JTabbedPane()

        # Tab 1: Sample Details
        form_view = self._create_form_view()
        self.tabbed_pane.addTab("Sample Details", form_view)

        # Tab 2: Timeline
        timeline_view = self._create_timeline_view()
        self.tabbed_pane.addTab("Timeline", timeline_view)

        # Tab 3: Sample Catalogue
        catalogue_view = self._create_catalogue_view()
        self.tabbed_pane.addTab("Sample Catalogue", catalogue_view)

        # Add tab change listener to refresh catalogue when opened
        self.tabbed_pane.addChangeListener(lambda e: self._on_tab_changed())

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
        """Create left panel with directory browser, badge, sample list, and action buttons"""
        panel = JPanel(BorderLayout())
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10))

        # Top section container - use GridBagLayout for precise control
        top_section = JPanel(GridBagLayout())
        gbc = GridBagConstraints()
        gbc.gridx = 0
        gbc.fill = GridBagConstraints.HORIZONTAL
        gbc.weightx = 1.0
        gbc.insets = Insets(0, 0, 0, 0)

        # Directory browser - path field on first line, buttons on second line
        dir_container = JPanel()
        dir_container.setLayout(BoxLayout(dir_container, BoxLayout.Y_AXIS))

        # Directory path field
        self.dir_label = JTextField("None")
        self.dir_label.setEditable(False)
        self.dir_label.setBackground(Color.WHITE)
        self.dir_label.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(Color(180, 180, 180), 1),
            BorderFactory.createEmptyBorder(3, 5, 3, 5)
        ))
        self.dir_label.setMaximumSize(Dimension(32767, 28))
        self.dir_label.setAlignmentX(Component.LEFT_ALIGNMENT)
        dir_container.add(self.dir_label)

        dir_container.add(Box.createVerticalStrut(3))

        # Browse button (full width)
        btn_browse = JButton('Browse...')
        btn_browse.setToolTipText("Browse for directory")
        btn_browse.addActionListener(lambda e: self._browse_directory())
        btn_browse.setAlignmentX(Component.LEFT_ALIGNMENT)
        btn_browse.setMaximumSize(Dimension(32767, 28))
        dir_container.add(btn_browse)

        dir_container.add(Box.createVerticalStrut(3))

        # Current dataset button (full width)
        btn_current = JButton('Go to current dataset')
        btn_current.setToolTipText("Navigate to current TopSpin dataset")
        btn_current.addActionListener(lambda e: self._navigate_to_curdata())
        btn_current.setAlignmentX(Component.LEFT_ALIGNMENT)
        btn_current.setMaximumSize(Dimension(32767, 28))
        dir_container.add(btn_current)

        gbc.gridy = 0
        top_section.add(dir_container, gbc)

        # Badge section - shows current sample status
        badge_panel = self._create_badge_panel()
        gbc.gridy = 1
        gbc.insets = Insets(10, 0, 10, 0)
        top_section.add(badge_panel, gbc)

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

        # Mouse listener for context menu and double-click
        self.sample_table.addMouseListener(SampleTableMouseListener(self))

        scroll_pane = JScrollPane(self.sample_table)
        panel.add(scroll_pane, BorderLayout.CENTER)

        # Bottom section - action buttons
        button_panel = self._create_action_buttons()
        panel.add(button_panel, BorderLayout.SOUTH)

        return panel

    def _create_badge_panel(self):
        """Create badge showing current sample status"""
        badge_container = JPanel()
        badge_container.setLayout(BoxLayout(badge_container, BoxLayout.Y_AXIS))

        # Main badge - pill-shaped with colored background
        self.badge_label = JLabel("EMPTY", JLabel.CENTER)
        self.badge_label.setFont(self.badge_label.getFont().deriveFont(Font.BOLD, 12.0))
        self.badge_label.setOpaque(True)
        self.badge_label.setBackground(Color(180, 180, 180))  # Grey for empty
        self.badge_label.setForeground(Color.WHITE)
        self.badge_label.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(Color(140, 140, 140), 2, True),  # Rounded border
            BorderFactory.createEmptyBorder(8, 15, 8, 15)
        ))
        self.badge_label.setAlignmentX(Component.CENTER_ALIGNMENT)

        # Make badge clickable
        self.badge_label.addMouseListener(BadgeClickListener(self))
        self.badge_label.setCursor(java.awt.Cursor.getPredefinedCursor(java.awt.Cursor.HAND_CURSOR))

        # Detail label - shows timestamp or other info
        self.badge_detail_label = JLabel("No active sample", JLabel.CENTER)
        self.badge_detail_label.setFont(self.badge_detail_label.getFont().deriveFont(Font.PLAIN, 10.0))
        self.badge_detail_label.setForeground(Color(100, 100, 100))
        self.badge_detail_label.setAlignmentX(Component.CENTER_ALIGNMENT)

        badge_container.add(self.badge_label)
        badge_container.add(Box.createVerticalStrut(5))
        badge_container.add(self.badge_detail_label)

        return badge_container

    def _create_action_buttons(self):
        """Create action button panel at bottom of sample list"""
        panel = JPanel()
        panel.setLayout(BoxLayout(panel, BoxLayout.Y_AXIS))
        panel.setBorder(BorderFactory.createEmptyBorder(10, 0, 0, 0))

        # First row: New | Duplicate
        row1 = JPanel(GridLayout(1, 2, 5, 0))
        self.btn_new = JButton('New...')
        self.btn_duplicate = JButton('Duplicate...')
        self.btn_new.setToolTipText("Create a new sample")
        self.btn_duplicate.setToolTipText("Duplicate the selected sample")
        self.btn_new.addActionListener(lambda e: self._new_sample())
        self.btn_duplicate.addActionListener(lambda e: self._duplicate_sample())
        # Green background for both New and Duplicate (primary actions)
        self.btn_new.setBackground(Color(200, 230, 200))
        self.btn_new.setOpaque(True)
        self.btn_duplicate.setBackground(Color(200, 230, 200))
        self.btn_duplicate.setOpaque(True)
        row1.add(self.btn_new)
        row1.add(self.btn_duplicate)

        # Second row: Edit
        row2 = JPanel(GridLayout(1, 1, 0, 0))
        self.btn_edit = JButton('Edit')
        self.btn_edit.setToolTipText("Edit the selected sample")
        self.btn_edit.addActionListener(lambda e: self._edit_sample())
        # Light blue background for Edit
        self.btn_edit.setBackground(Color(220, 235, 255))
        self.btn_edit.setOpaque(True)
        row2.add(self.btn_edit)

        # Third row: Mark as ejected
        row3 = JPanel(GridLayout(1, 1, 0, 0))
        self.btn_eject = JButton('Mark as ejected')
        self.btn_eject.setToolTipText("Mark active sample as ejected")
        self.btn_eject.addActionListener(lambda e: self._eject_active_sample())
        # Yellow/amber background for Eject (warning)
        self.btn_eject.setBackground(Color(255, 235, 180))
        self.btn_eject.setOpaque(True)
        row3.add(self.btn_eject)

        # Fourth row: Delete
        row4 = JPanel(GridLayout(1, 1, 0, 0))
        self.btn_delete = JButton('Delete')
        self.btn_delete.setToolTipText("Delete the selected sample (must be ejected)")
        self.btn_delete.addActionListener(lambda e: self._delete_sample())
        # Light red background for Delete (destructive)
        self.btn_delete.setBackground(Color(255, 220, 220))
        self.btn_delete.setOpaque(True)
        row4.add(self.btn_delete)

        # Fifth row: Settings
        row5 = JPanel(GridLayout(1, 1, 0, 0))
        btn_settings = JButton('Settings...')
        btn_settings.setToolTipText("Configure search directories and preferences")
        btn_settings.addActionListener(lambda e: self._show_settings())
        # Light grey background for Settings
        btn_settings.setBackground(Color(240, 240, 240))
        btn_settings.setOpaque(True)
        row5.add(btn_settings)

        panel.add(row1)
        panel.add(Box.createVerticalStrut(5))
        panel.add(row2)
        panel.add(Box.createVerticalStrut(5))
        panel.add(row3)
        panel.add(Box.createVerticalStrut(5))
        panel.add(row4)
        panel.add(Box.createVerticalStrut(5))
        panel.add(row5)

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

        # Make Save button visually primary with color
        self.btn_save.setFont(self.btn_save.getFont().deriveFont(Font.BOLD))
        self.btn_save.setBackground(Color(200, 230, 200))  # Green
        self.btn_save.setOpaque(True)

        button_row.add(self.btn_cancel)
        button_row.add(self.btn_save)

        form_button_panel.add(button_row, BorderLayout.EAST)
        panel.add(form_button_panel, BorderLayout.SOUTH)

        return panel

    def _create_timeline_view(self):
        """Create timeline view panel with table"""
        panel = JPanel(BorderLayout())
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10))

        # Top panel with utility buttons
        top_panel = JPanel(BorderLayout())

        # Left side: view/edit buttons
        left_panel = JPanel(FlowLayout(FlowLayout.LEFT))

        self.view_sample_btn = JButton("View/edit sample")
        self.view_sample_btn.setEnabled(False)
        self.view_sample_btn.addActionListener(lambda e: self._view_sample_from_timeline())
        left_panel.add(self.view_sample_btn)

        self.open_experiment_btn = JButton("Open experiment in Topspin")
        self.open_experiment_btn.setEnabled(False)
        self.open_experiment_btn.addActionListener(lambda e: self._open_experiment_from_timeline())
        left_panel.add(self.open_experiment_btn)

        top_panel.add(left_panel, BorderLayout.WEST)

        # Right side: refresh button
        right_panel = JPanel(FlowLayout(FlowLayout.RIGHT))
        btn_refresh = JButton('Refresh', actionPerformed=lambda e: self._refresh_timeline())
        right_panel.add(btn_refresh)
        top_panel.add(right_panel, BorderLayout.EAST)

        panel.add(top_panel, BorderLayout.NORTH)

        # Timeline table
        self.timeline_table_model = TimelineTableModel()
        self.timeline_table = JTable(self.timeline_table_model)
        self.timeline_table.setRowHeight(28)
        self.timeline_table.setShowGrid(True)
        self.timeline_table.setGridColor(Color(230, 230, 230))
        self.timeline_table.setAutoCreateRowSorter(True)

        # Custom renderer for highlighting
        self.timeline_table.setDefaultRenderer(Object, TimelineTableCellRenderer(self))

        # Double-click listener
        self.timeline_table.addMouseListener(TimelineMouseListener(self))

        # Selection listener to update button state
        self.timeline_table.getSelectionModel().addListSelectionListener(
            lambda e: self._update_timeline_selection_state() if not e.getValueIsAdjusting() else None
        )

        scroll_pane = JScrollPane(self.timeline_table)
        panel.add(scroll_pane, BorderLayout.CENTER)

        # Bottom panel with reassignment action buttons
        bottom_panel = JPanel(FlowLayout(FlowLayout.LEFT))

        self.create_from_selection_btn = JButton("Create sample from selection")
        self.create_from_selection_btn.setEnabled(False)
        self.create_from_selection_btn.addActionListener(lambda e: self._create_sample_from_experiments())
        bottom_panel.add(self.create_from_selection_btn)

        self.reassign_prev_btn = JButton("Reassign to previous sample")
        self.reassign_prev_btn.setEnabled(False)
        self.reassign_prev_btn.addActionListener(lambda e: self._reassign_to_previous_sample())
        bottom_panel.add(self.reassign_prev_btn)

        self.reassign_next_btn = JButton("Reassign to next sample")
        self.reassign_next_btn.setEnabled(False)
        self.reassign_next_btn.addActionListener(lambda e: self._reassign_to_next_sample())
        bottom_panel.add(self.reassign_next_btn)

        panel.add(bottom_panel, BorderLayout.SOUTH)

        return panel

    def _create_catalogue_view(self):
        """Create catalogue view panel with searchable sample table"""
        panel = JPanel(BorderLayout())
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10))

        # Top panel with search bar and refresh button
        top_panel = JPanel(BorderLayout())
        top_panel.setBorder(BorderFactory.createEmptyBorder(0, 0, 10, 0))

        # Search panel on the left
        search_panel = JPanel(FlowLayout(FlowLayout.LEFT, 0, 0))
        search_label = JLabel("Search: ")
        search_label.setFont(search_label.getFont().deriveFont(Font.PLAIN, 11.0))
        search_panel.add(search_label)

        self.catalogue_search_field = JTextField(30)
        self.catalogue_search_field.setPreferredSize(Dimension(300, 26))
        self.catalogue_search_field.getDocument().addDocumentListener(CatalogueSearchListener(self))
        search_panel.add(self.catalogue_search_field)

        top_panel.add(search_panel, BorderLayout.WEST)

        # Refresh button on the right
        btn_refresh = JButton('Refresh', actionPerformed=lambda e: self._refresh_catalogue())
        top_panel.add(btn_refresh, BorderLayout.EAST)

        panel.add(top_panel, BorderLayout.NORTH)

        # Catalogue table
        self.catalogue_table_model = CatalogueTableModel()
        self.catalogue_table = JTable(self.catalogue_table_model)
        self.catalogue_table.setRowHeight(26)
        self.catalogue_table.setShowGrid(True)
        self.catalogue_table.setGridColor(Color(230, 230, 230))
        self.catalogue_table.setAutoCreateRowSorter(True)
        self.catalogue_table.setAutoResizeMode(JTable.AUTO_RESIZE_OFF)  # Allow horizontal scrolling

        # Set column widths
        col_model = self.catalogue_table.getColumnModel()
        col_model.getColumn(0).setPreferredWidth(100)  # Created
        col_model.getColumn(1).setPreferredWidth(200)  # Experiment
        col_model.getColumn(2).setPreferredWidth(150)  # Label
        col_model.getColumn(3).setPreferredWidth(250)  # Components
        col_model.getColumn(4).setPreferredWidth(250)  # Buffer
        col_model.getColumn(5).setPreferredWidth(120)  # Tube
        col_model.getColumn(6).setPreferredWidth(200)  # Notes
        col_model.getColumn(7).setPreferredWidth(120)  # Users

        # Custom renderer for tooltips
        self.catalogue_table.setDefaultRenderer(Object, CatalogueTableCellRenderer())

        # Selection listener to enable/disable buttons
        self.catalogue_table.getSelectionModel().addListSelectionListener(
            lambda e: self._on_catalogue_selection_changed() if not e.getValueIsAdjusting() else None
        )

        # Double-click listener to navigate to sample
        self.catalogue_table.addMouseListener(CatalogueMouseListener(self))

        # Create a CardLayout panel to switch between table and empty state
        self.catalogue_center_panel = JPanel(CardLayout())

        # Table view
        scroll_pane = JScrollPane(self.catalogue_table)
        scroll_pane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED)
        self.catalogue_center_panel.add(scroll_pane, "TABLE")

        # Empty state view
        empty_panel = self._create_catalogue_empty_state()
        self.catalogue_center_panel.add(empty_panel, "EMPTY")

        panel.add(self.catalogue_center_panel, BorderLayout.CENTER)

        # Bottom panel with action buttons
        bottom_panel = JPanel(FlowLayout(FlowLayout.LEFT, 5, 5))
        bottom_panel.setBorder(BorderFactory.createEmptyBorder(5, 0, 0, 0))

        self.catalogue_btn_view = JButton('View', actionPerformed=lambda e: self._catalogue_view_selected())
        self.catalogue_btn_view.setEnabled(False)
        self.catalogue_btn_view.setToolTipText("View selected sample (read-only)")
        bottom_panel.add(self.catalogue_btn_view)

        self.catalogue_btn_edit = JButton('Edit', actionPerformed=lambda e: self._catalogue_edit_selected())
        self.catalogue_btn_edit.setEnabled(False)
        self.catalogue_btn_edit.setToolTipText("Edit selected sample")
        bottom_panel.add(self.catalogue_btn_edit)

        self.catalogue_btn_duplicate = JButton('Duplicate into current experiment', actionPerformed=lambda e: self._catalogue_duplicate_selected())
        self.catalogue_btn_duplicate.setEnabled(False)
        self.catalogue_btn_duplicate.setToolTipText("Duplicate selected sample into the current experiment directory")
        bottom_panel.add(self.catalogue_btn_duplicate)

        panel.add(bottom_panel, BorderLayout.SOUTH)

        return panel

    def _create_catalogue_empty_state(self):
        """Create empty state panel shown when no root directories are configured"""
        panel = JPanel()
        panel.setLayout(BoxLayout(panel, BoxLayout.Y_AXIS))
        panel.setBorder(BorderFactory.createEmptyBorder(50, 20, 50, 20))

        # Message
        message_label = JLabel("No search directories configured")
        message_label.setFont(message_label.getFont().deriveFont(Font.BOLD, 16.0))
        message_label.setAlignmentX(Component.CENTER_ALIGNMENT)
        panel.add(message_label)

        panel.add(Box.createVerticalStrut(10))

        # Instructions
        instructions = JLabel("Please add search directories using the Settings button")
        instructions.setFont(instructions.getFont().deriveFont(Font.PLAIN, 12.0))
        instructions.setForeground(Color(100, 100, 100))
        instructions.setAlignmentX(Component.CENTER_ALIGNMENT)
        panel.add(instructions)

        panel.add(Box.createVerticalStrut(20))

        # Settings button
        btn_settings = JButton('Settings...', actionPerformed=lambda e: self._show_settings())
        btn_settings.setAlignmentX(Component.CENTER_ALIGNMENT)
        panel.add(btn_settings)

        return panel

    def _create_status_panel(self):
        """Create bottom status panel"""
        panel = JPanel(BorderLayout())

        # Left side - status
        left_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        left_panel.add(JLabel("Status:"))
        self.status_label = JLabel("Ready")
        left_panel.add(self.status_label)
        panel.add(left_panel, BorderLayout.WEST)

        # Center - update indicator (initially hidden)
        center_panel = JPanel(FlowLayout(FlowLayout.CENTER))
        self.update_label = JLabel("")
        self.update_label.setVisible(False)
        self.update_label.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR))
        center_panel.add(self.update_label)
        panel.add(center_panel, BorderLayout.CENTER)

        # Right side - repository link
        right_panel = JPanel(FlowLayout(FlowLayout.RIGHT))
        repo_link = JLabel("<html><a href=''>View Documentation...</a></html>")
        repo_link.setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR))
        repo_link.setToolTipText("https://nmr-samples.github.io/topspin/")

        # Add click listener to open URL
        def open_repo(event):
            try:
                import java.awt.Desktop as Desktop
                import java.net.URI as URI
                if Desktop.isDesktopSupported():
                    desktop = Desktop.getDesktop()
                    if desktop.isSupported(Desktop.Action.BROWSE):
                        desktop.browse(URI("https://nmr-samples.github.io/topspin/"))
            except Exception as e:
                MSG("Could not open browser: %s" % str(e))

        # MouseAdapter is an abstract Java class; instantiate a concrete
        # subclass that implements mouseClicked and forwards to our handler.
        class RepoMouseAdapter(java.awt.event.MouseAdapter):
            def __init__(self, handler):
                self._handler = handler

            def mouseClicked(self, event):
                try:
                    self._handler(event)
                except Exception as e:
                    MSG("Could not open browser: %s" % str(e))

        repo_link.addMouseListener(RepoMouseAdapter(open_repo))
        right_panel.add(repo_link)
        panel.add(right_panel, BorderLayout.EAST)

        # Add click handler for update indicator
        def show_update_instructions(event):
            msg = ("Updates are available!\n\n"
                   "To update, run the following command in the installation directory:\n\n"
                   "git pull\n\n"
                   "Installation directory:\n%s") % self.script_dir
            JOptionPane.showMessageDialog(
                self.frame,
                msg,
                "Update Available",
                JOptionPane.INFORMATION_MESSAGE
            )

        class UpdateMouseAdapter(java.awt.event.MouseAdapter):
            def __init__(self, handler):
                self._handler = handler

            def mouseClicked(self, event):
                try:
                    self._handler(event)
                except Exception as e:
                    MSG("Error: %s" % str(e))

        self.update_label.addMouseListener(UpdateMouseAdapter(show_update_instructions))

        return panel

    def _update_update_indicator(self, has_updates, error_msg, debug_info):
        """Update the update indicator in the status bar

        Args:
            has_updates: True if updates available, False if up to date, None if error
            error_msg: Error message if has_updates is None
            debug_info: Debug information to display
        """
        if has_updates is True:
            self.update_label.setText("<html><a href=''>Update Available - Click for Instructions</a></html>")
            self.update_label.setForeground(Color(255, 140, 0))  # Orange
            self.update_label.setVisible(True)
        elif has_updates is False:
            # Up to date - hide the indicator
            self.update_label.setVisible(False)
        else:
            # Error checking for updates - don't show anything to avoid clutter
            self.update_label.setVisible(False)

    def _navigate_to_curdata(self):
        """Navigate to current TopSpin dataset directory"""
        try:
            # CURDATA must be run in a command thread via EXEC_PYSCRIPT
            # We navigate to the parent directory (not the expno subdirectory)
            EXEC_PYSCRIPT('''
import os
curdata = CURDATA()
if curdata:
    name = curdata[0]
    expno = str(curdata[1])  # Experiment number
    directory = curdata[3]
    # Navigate to the dataset directory (parent of expno folders)
    full_path = os.path.join(directory, name)
    # Get the app and set directory with expno for auto-selection
    from java.lang import System
    app = System.getProperties().get("org.nmr-samples.topspin")
    if app:
        app.set_directory(full_path, expno)
''')
        except Exception as e:
            self.update_status("Could not navigate to CURDATA: %s" % str(e))

    def _check_directory_matches_curdata(self, callback=None, auto_select_after_nav=True):
        """Check if current directory matches current TopSpin dataset, offer to change if not.

        Args:
            callback: Optional function to call after navigation (if user chooses to navigate)
            auto_select_after_nav: Whether to auto-select a sample after navigation (default True)

        Returns:
            bool: True to proceed with operation, False to cancel
        """
        try:
            EXEC_PYSCRIPT('''
import os
curdata = CURDATA()
if curdata:
    name = curdata[0]
    directory = curdata[3]
    curdata_path = os.path.join(directory, name)

    from java.lang import System
    app = System.getProperties().get("org.nmr-samples.topspin")
    if app:
        app._store_curdata_check_result(curdata_path)
''')

            # Give EXEC_PYSCRIPT time to execute
            import time
            time.sleep(0.2)

            # Check stored result
            if not hasattr(self, '_curdata_check_result'):
                # Could not determine current dataset - assume OK to proceed
                return True

            curdata_path = self._curdata_check_result
            delattr(self, '_curdata_check_result')  # Clean up

            if curdata_path == self.current_directory:
                # Directories match - all good
                return True

            # Get short directory names for display
            current_parts = self.current_directory.split(os.sep)
            curdata_parts = curdata_path.split(os.sep)
            current_display = os.sep.join(current_parts[-2:]) if len(current_parts) >= 2 else self.current_directory
            curdata_display = os.sep.join(curdata_parts[-2:]) if len(curdata_parts) >= 2 else curdata_path

            # Directories don't match - offer to change
            result = JOptionPane.showConfirmDialog(
                self.frame,
                "Sample manager is in:\n  %s\n\nCurrent TopSpin dataset is:\n  %s\n\nSwitch to current dataset folder?" % (
                    current_display, curdata_display
                ),
                "Switch Directory?",
                JOptionPane.YES_NO_OPTION,
                JOptionPane.QUESTION_MESSAGE
            )

            if result == JOptionPane.YES_OPTION:
                # User wants to change - navigate to current dataset
                # Store flag for navigation to check
                self._skip_auto_select = not auto_select_after_nav
                self._navigate_to_curdata()
                # Give navigation time to complete
                time.sleep(0.2)
                # Call the callback to continue the operation
                if callback:
                    callback()
                return False  # Indicate we handled it via callback
            else:
                # User declined - proceed with current directory
                return True

        except Exception as e:
            # On error, assume OK to proceed
            self.update_status("Could not check current dataset: %s" % str(e))
            return True

    def _store_curdata_check_result(self, curdata_path):
        """Store CURDATA check result (called from EXEC_PYSCRIPT)"""
        self._curdata_check_result = curdata_path

    def check_and_switch_to_curdata(self):
        """Public method for external scripts to check and switch to CURDATA if needed.

        Returns:
            bool: True if directories match or user switched, False if user declined
        """
        try:
            EXEC_PYSCRIPT('''
import os
curdata = CURDATA()
if curdata:
    name = curdata[0]
    directory = curdata[3]
    curdata_path = os.path.join(directory, name)

    from java.lang import System
    app = System.getProperties().get("org.nmr-samples.topspin")
    if app:
        app._store_curdata_check_result(curdata_path)
''')

            # Give EXEC_PYSCRIPT time to execute
            import time
            time.sleep(0.2)

            # Check stored result
            if not hasattr(self, '_curdata_check_result'):
                # Could not determine current dataset - assume OK
                return True

            curdata_path = self._curdata_check_result
            delattr(self, '_curdata_check_result')  # Clean up

            if curdata_path == self.current_directory:
                # Directories match - all good
                return True

            # Get short directory names for display
            current_parts = self.current_directory.split(os.sep)
            curdata_parts = curdata_path.split(os.sep)
            current_display = os.sep.join(current_parts[-2:]) if len(current_parts) >= 2 else self.current_directory
            curdata_display = os.sep.join(curdata_parts[-2:]) if len(curdata_parts) >= 2 else curdata_path

            # Directories don't match - offer to change
            from javax.swing import JOptionPane
            result = JOptionPane.showConfirmDialog(
                self.frame,
                "Sample manager is in:\n  %s\n\nCurrent TopSpin dataset is:\n  %s\n\nSwitch to current dataset folder?" % (
                    current_display, curdata_display
                ),
                "Switch Directory?",
                JOptionPane.YES_NO_OPTION,
                JOptionPane.QUESTION_MESSAGE
            )

            if result == JOptionPane.YES_OPTION:
                # User wants to change - navigate to current dataset
                # Don't auto-select after navigation for injection commands
                self._skip_auto_select = True
                self._navigate_to_curdata()
                # Give navigation time to complete
                time.sleep(0.2)
                return True
            else:
                # User declined to switch
                return False

        except Exception as e:
            # On error, assume OK to proceed
            self.update_status("Could not check current dataset: %s" % str(e))
            return True

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

    def set_directory(self, directory, expno=None, auto_select=True):
        """Set current directory and refresh sample list

        Args:
            directory: Directory path to navigate to
            expno: Optional experiment number (as string) for auto-selection
            auto_select: Whether to auto-select a sample
        """
        self.current_directory = directory

        # Show only last two directory components for cleaner display
        dir_parts = directory.split(os.sep)
        if len(dir_parts) >= 2:
            display_dir = os.sep.join(dir_parts[-2:])
        else:
            display_dir = directory

        self.dir_label.setText(display_dir)
        self.dir_label.setToolTipText(directory)  # Full path in tooltip

        self._refresh_sample_list()
        self._refresh_timeline()
        self._update_badge()

        # Check if we should skip auto-select (set by _check_directory_matches_curdata)
        skip_auto_select = getattr(self, '_skip_auto_select', False)
        if skip_auto_select:
            # Clear the flag
            delattr(self, '_skip_auto_select')
            auto_select = False

        # Auto-select appropriate sample if requested
        if auto_select:
            self._auto_select_sample_for_directory(expno)

        self.update_status("Directory: %s" % directory)

    def _auto_select_sample_for_directory(self, expno=None):
        """Auto-select the sample associated with current experiment via timeline or timestamp

        Args:
            expno: Optional experiment number (as string) for sample selection

        If expno is provided, selects the sample that was active during that experiment.
        If expno is None, selects the active sample or most recently created/modified sample.
        """
        print("DEBUG: _auto_select_sample_for_directory called with expno=%s" % expno)

        if not self.current_directory:
            print("DEBUG: No current directory, returning")
            return

        try:
            # Convert expno from string to int if provided
            if expno is not None:
                try:
                    expno = int(expno)
                    print("DEBUG: Converted expno to int: %d" % expno)
                except (ValueError, TypeError):
                    print("DEBUG: Invalid expno, falling back to active/recent")
                    # Invalid expno - select active sample or most recent
                    self._select_active_or_recent_sample()
                    return
            else:
                print("DEBUG: No expno provided, falling back to active/recent")
                # No expno provided - select active sample or most recent
                self._select_active_or_recent_sample()
                return

            # Build timeline to find which sample was active during this experiment
            entries = self.timeline_builder.build_timeline(self.current_directory)
            print("DEBUG: Built timeline with %d entries" % len(entries))

            # Find the sample that was active when this experiment was run
            # Timeline is sorted chronologically, so we look for:
            # 1. The most recent sample_created BEFORE this experiment number
            # 2. Make sure it wasn't ejected before this experiment

            best_sample_filepath = None
            current_sample_filepath = None

            for entry in entries:
                if entry.entry_type == 'sample_created':
                    # New sample became active
                    current_sample_filepath = entry.filepath
                    print("DEBUG: Sample created: %s" % entry.filepath)
                elif entry.entry_type == 'sample_ejected':
                    # Sample was ejected, no longer active
                    print("DEBUG: Sample ejected: %s" % current_sample_filepath)
                    current_sample_filepath = None
                elif entry.entry_type == 'experiment':
                    # Check if this is our target experiment
                    try:
                        entry_expno = int(entry.name)
                        print("DEBUG: Found experiment %d (looking for %d)" % (entry_expno, expno))
                        if entry_expno == expno:
                            # This is the experiment we want
                            # The current_sample_filepath is the sample that was active
                            best_sample_filepath = current_sample_filepath
                            print("DEBUG: Found target experiment! Best sample: %s" % best_sample_filepath)
                            break
                    except (ValueError, AttributeError):
                        continue

            # Find this sample in the table and select it
            if best_sample_filepath:
                print("DEBUG: Looking for sample in table: %s" % best_sample_filepath)
                sample_files = self.sample_io.list_sample_files(self.current_directory)
                for idx, filename in enumerate(sample_files):
                    filepath = os.path.join(self.current_directory, filename)
                    if filepath == best_sample_filepath:
                        print("DEBUG: Found sample at index %d, selecting..." % idx)
                        self.sample_table.setRowSelectionInterval(idx, idx)
                        # Scroll to make it visible
                        self.sample_table.scrollRectToVisible(
                            self.sample_table.getCellRect(idx, 0, True)
                        )
                        # IMPORTANT: Actually load and display the sample
                        self._on_sample_selected()
                        print("DEBUG: Sample selected and loaded")
                        break
            else:
                print("DEBUG: No best_sample_filepath found")

        except Exception as e:
            # Silently fail - auto-selection is a convenience feature
            print("DEBUG: Exception in _auto_select_sample_for_directory: %s" % str(e))
            pass

    def _select_active_or_recent_sample(self):
        """Select the active sample, or if none, the most recently created/modified sample"""
        print("DEBUG: _select_active_or_recent_sample called")

        if not self.current_directory:
            print("DEBUG: No current directory")
            return

        try:
            sample_files = self.sample_io.list_sample_files(self.current_directory)
            print("DEBUG: Found %d sample files" % len(sample_files))

            if not sample_files:
                print("DEBUG: No sample files found")
                return

            # First, look for an active (loaded) sample
            for idx, filename in enumerate(sample_files):
                filepath = os.path.join(self.current_directory, filename)
                status = self.sample_io.get_sample_status(filepath)
                print("DEBUG: Sample %d (%s) has status: %s" % (idx, filename, status))
                if status == 'loaded':
                    print("DEBUG: Found loaded sample at index %d, selecting..." % idx)
                    self.sample_table.setRowSelectionInterval(idx, idx)
                    self.sample_table.scrollRectToVisible(
                        self.sample_table.getCellRect(idx, 0, True)
                    )
                    # IMPORTANT: Actually load and display the sample
                    self._on_sample_selected()
                    print("DEBUG: Loaded sample selected and displayed")
                    return

            # No active sample - select the most recent by timestamp
            # Find sample with most recent created or modified timestamp
            print("DEBUG: No loaded sample found, looking for most recent")
            most_recent_idx = 0
            most_recent_time = None

            for idx, filename in enumerate(sample_files):
                filepath = os.path.join(self.current_directory, filename)
                data = self.sample_io.read_sample(filepath)
                if data:
                    metadata = data.get('Metadata', {})
                    # Use modified timestamp if available, otherwise created
                    timestamp = metadata.get('modified_timestamp') or metadata.get('created_timestamp')
                    if timestamp:
                        if most_recent_time is None or timestamp > most_recent_time:
                            most_recent_time = timestamp
                            most_recent_idx = idx

            # Select the most recent sample
            if most_recent_time is not None:
                print("DEBUG: Most recent sample is at index %d, selecting..." % most_recent_idx)
                self.sample_table.setRowSelectionInterval(most_recent_idx, most_recent_idx)
                self.sample_table.scrollRectToVisible(
                    self.sample_table.getCellRect(most_recent_idx, 0, True)
                )
                # IMPORTANT: Actually load and display the sample
                self._on_sample_selected()
                print("DEBUG: Most recent sample selected and displayed")
            else:
                print("DEBUG: No timestamped samples found")

        except Exception as e:
            # Silently fail - auto-selection is a convenience feature
            print("DEBUG: Exception in _select_active_or_recent_sample: %s" % str(e))
            pass

    def _get_active_sample(self):
        """Get the currently active sample (if any)"""
        if not self.current_directory:
            return None

        try:
            sample_files = self.sample_io.list_sample_files(self.current_directory)
            for filename in sample_files:
                filepath = os.path.join(self.current_directory, filename)
                status = self.sample_io.get_sample_status(filepath)
                if status == 'loaded':  # Active sample
                    data = self.sample_io.read_sample(filepath)
                    return {
                        'filename': filename,
                        'filepath': filepath,
                        'data': data,
                        'label': data.get('sample', {}).get('label', filename),
                        'created': data.get('metadata', {}).get('created_timestamp', '')
                    }
        except:
            pass
        return None

    def _has_previous_samples(self):
        """Check if there are any previous samples (for duplication)"""
        if not self.current_directory:
            return False

        try:
            sample_files = self.sample_io.list_sample_files(self.current_directory)
            return len(sample_files) > 0
        except:
            return False

    def _get_last_sample(self):
        """Get the most recent sample (by creation time) for duplication"""
        if not self.current_directory:
            return None

        try:
            sample_files = self.sample_io.list_sample_files(self.current_directory)
            if not sample_files:
                return None

            # Files are already sorted chronologically (newest last)
            last_filename = sample_files[-1]
            filepath = os.path.join(self.current_directory, last_filename)
            data = self.sample_io.read_sample(filepath)

            return {
                'filename': last_filename,
                'filepath': filepath,
                'data': data
            }
        except:
            return None

    def _new_sample_with_timestamp(self, timestamp):
        """Create new sample with a specific injection timestamp"""
        # Set draft state first
        self.current_sample_file = None
        self.is_draft = True
        self.draft_data = {'metadata': {'created_timestamp': timestamp.isoformat() + 'Z'}}
        self.form_modified = False

        # Update badge and refresh sample list to show draft
        self._update_badge()
        self._refresh_sample_list()

        # Create fresh form generator using CURRENT schema for new samples
        self.form_generator = SchemaFormGenerator(self.current_schema_path)

        # Create empty form
        self.form_panel.removeAll()
        form_scroll = self.form_generator.create_form_panel(self)
        self.form_panel.add(form_scroll, BorderLayout.CENTER)
        self.form_panel.revalidate()
        self.form_panel.repaint()

        # Set button states
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)
        self.btn_save.setEnabled(False)
        self.btn_cancel.setEnabled(True)

        self.tabbed_pane.setSelectedIndex(0)  # Switch to Sample Details tab

    def _duplicate_last_sample_with_timestamp(self, timestamp):
        """Duplicate the last sample with a specific injection timestamp"""
        last_sample = self._get_last_sample()
        if not last_sample:
            MSG("No previous samples to duplicate")
            return

        try:
            data = last_sample['data']

            # Append "(copy)" to label
            if 'sample' in data and 'label' in data['sample']:
                data['sample']['label'] = data['sample']['label'] + " (copy)"

            # Set metadata timestamps
            if 'metadata' not in data:
                data['metadata'] = {}

            data['metadata']['created_timestamp'] = timestamp.isoformat() + 'Z'
            data['metadata'].pop('modified_timestamp', None)
            data['metadata'].pop('ejected_timestamp', None)
            data['metadata'].pop('schema_version', None)

            # Set draft state first
            self.current_sample_file = None
            self.is_draft = True
            self.draft_data = data
            self.form_modified = False

            # Update badge and refresh sample list to show draft
            self._update_badge()
            self._refresh_sample_list()

            # Create fresh form generator using CURRENT schema for duplicates
            self.form_generator = SchemaFormGenerator(self.current_schema_path)

            # Create form first
            self.form_panel.removeAll()
            form_scroll = self.form_generator.create_form_panel(self)
            self.form_panel.add(form_scroll, BorderLayout.CENTER)
            self.form_panel.revalidate()
            self.form_panel.repaint()

            # Then populate with data
            self.form_generator.load_data(data)

            # Set button states
            self.btn_save.setVisible(True)
            self.btn_cancel.setVisible(True)
            self.btn_save.setEnabled(False)
            self.btn_cancel.setEnabled(True)

            self.tabbed_pane.setSelectedIndex(0)  # Switch to Sample Details tab

        except Exception as e:
            MSG("Error duplicating sample: %s" % str(e))

    def _update_badge(self):
        """Update the badge to reflect current sample status"""
        if self.is_draft:
            # Draft state - unsaved sample
            sample_label = "New Sample"
            if self.draft_data:
                sample_label = self.draft_data.get('sample', {}).get('label', 'New Sample')

            self.badge_label.setText("DRAFT  " + str(sample_label))
            self.badge_label.setBackground(Color(218, 165, 32))  # Amber/gold
            self.badge_label.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(Color(184, 134, 11), 2, True),
                BorderFactory.createEmptyBorder(8, 15, 8, 15)
            ))
            self.badge_detail_label.setText("Unsaved changes")
            self.btn_eject.setEnabled(False)  # Can't eject a draft
        else:
            active = self._get_active_sample()
            if active:
                # Active sample loaded
                self.badge_label.setText("ACTIVE  " + str(active['label']))
                self.badge_label.setBackground(Color(34, 139, 34))  # Forest green
                self.badge_label.setBorder(BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(Color(0, 100, 0), 2, True),
                    BorderFactory.createEmptyBorder(8, 15, 8, 15)
                ))

                # Format timestamp - convert UTC to local time for display
                created = active['created']
                if created:
                    try:
                        import calendar
                        # Parse UTC timestamp
                        dt_utc = datetime.strptime(created[:19], "%Y-%m-%dT%H:%M:%S")
                        # Convert to local time
                        utc_timestamp = calendar.timegm(dt_utc.timetuple())
                        dt_local = datetime.fromtimestamp(utc_timestamp)
                        time_str = dt_local.strftime("%I:%M %p").lstrip('0')
                        self.badge_detail_label.setText("Loaded: " + time_str)
                    except:
                        self.badge_detail_label.setText("Loaded")
                else:
                    self.badge_detail_label.setText("Loaded")

                self.btn_eject.setEnabled(True)  # Only enable eject when there's an active sample
            else:
                # Empty - no active sample
                self.badge_label.setText("EMPTY")
                self.badge_label.setBackground(Color(180, 180, 180))  # Grey
                self.badge_label.setBorder(BorderFactory.createCompoundBorder(
                    BorderFactory.createLineBorder(Color(140, 140, 140), 2, True),
                    BorderFactory.createEmptyBorder(8, 15, 8, 15)
                ))

                # Show last ejected sample if any
                try:
                    sample_files = self.sample_io.list_sample_files(self.current_directory)
                    if sample_files:
                        # Find most recently ejected
                        last_ejected = None
                        last_time = None
                        for filename in sample_files:
                            filepath = os.path.join(self.current_directory, filename)
                            data = self.sample_io.read_sample(filepath)
                            ejected = data.get('metadata', {}).get('ejected_timestamp')
                            if ejected:
                                if last_time is None or ejected > last_time:
                                    last_time = ejected
                                    last_ejected = data.get('sample', {}).get('label', filename)

                        if last_ejected:
                            self.badge_detail_label.setText("Last: " + str(last_ejected))
                        else:
                            self.badge_detail_label.setText("No active sample")
                    else:
                        self.badge_detail_label.setText("No samples")
                except:
                    self.badge_detail_label.setText("No active sample")

                self.btn_eject.setEnabled(False)

    def _refresh_sample_list(self):
        """Refresh the sample list from current directory"""
        if not self.current_directory:
            self.sample_table_model.clear_rows()
            self._update_badge()
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
                    label = data.get('sample', {}).get('label', filename)
                    created = data.get('metadata', {}).get('created_timestamp', '')
                    users = data.get('people', {}).get('users', [])
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
                    'filepath': filepath,
                    'is_draft': False
                })

            # Add draft as last row if it exists (chronologically last)
            if self.is_draft:
                draft_label = "<new sample>"
                if self.draft_data:
                    sample_label = self.draft_data.get('sample', {}).get('label', '')
                    if sample_label:
                        # Check if it's a copy
                        if sample_label.endswith(' (copy)'):
                            draft_label = "<copy of %s>" % sample_label[:-7]  # Remove " (copy)"
                        else:
                            draft_label = "<%s>" % sample_label

                rows.append({
                    'status': 'draft',
                    'label': draft_label,
                    'filename': None,  # No file yet
                    'created': '',
                    'users': [],
                    'filepath': None,
                    'is_draft': True
                })

            self.sample_table_model.set_rows(rows)
            self._update_badge()  # Update badge after refreshing list

        except Exception as e:
            self.update_status("Error refreshing sample list: %s" % str(e))

    def _get_schema_path_for_version(self, version):
        """Get schema path for a specific version

        Returns:
            str: Path to schema file, or None if not found
        """
        # Try to load the specific version
        versioned_path = os.path.join(self.script_dir, 'schemas', 'versions', 'v%s' % version, 'schema.json')
        if os.path.exists(versioned_path):
            return versioned_path

        # Schema version not found
        return None

    def _create_schema_error_panel(self, schema_version):
        """Create a panel displaying a schema version error

        Args:
            schema_version: The schema version that was not found

        Returns:
            JPanel: Panel with error message
        """
        from javax.swing import JPanel, JLabel, BorderFactory
        from java.awt import BorderLayout, Color, Font

        error_panel = JPanel(BorderLayout())
        error_panel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20))

        # Create message panel
        message_panel = JPanel()
        message_panel.setLayout(BoxLayout(message_panel, BoxLayout.Y_AXIS))

        # Title
        title = JLabel("Schema Version Not Found")
        title.setFont(Font("SansSerif", Font.BOLD, 16))
        title.setForeground(Color(200, 50, 50))
        title.setAlignmentX(Component.CENTER_ALIGNMENT)
        message_panel.add(title)
        message_panel.add(Box.createVerticalStrut(20))

        # Details
        details = JLabel("<html><div style='text-align: center;'>"
                        "This sample requires schema version <b>%s</b><br><br>"
                        "Expected location:<br>"
                        "<code>schemas/versions/v%s/schema.json</code><br><br>"
                        "Please update your installation to receive<br>"
                        "the missing schema files."
                        "</div></html>" % (schema_version, schema_version))
        details.setAlignmentX(Component.CENTER_ALIGNMENT)
        message_panel.add(details)

        error_panel.add(message_panel, BorderLayout.CENTER)
        return error_panel

    def _on_sample_selected(self):
        """Handle sample selection - show read-only view"""
        selected_row = self.sample_table.getSelectedRow()
        if selected_row < 0:
            self.btn_duplicate.setEnabled(False)
            self.btn_edit.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.selected_sample_filepath = None
            # Clear form view
            self._show_placeholder()
            # Refresh timeline to clear highlighting
            self.timeline_table.repaint()
            return

        # Get row data
        row_data = self.sample_table_model.get_row(selected_row)
        is_draft = row_data.get('is_draft', False)

        # If this is a draft row, ignore selection (draft is already being edited)
        if is_draft:
            # Don't change anything - draft is already in edit mode
            return

        filename = row_data['filename']
        status = row_data['status']
        self.current_sample_file = filename
        self.selected_sample_filepath = row_data['filepath']

        # Enable/disable buttons based on sample status
        self.btn_duplicate.setEnabled(True)
        self.btn_edit.setEnabled(True)

        # Eject button - only enabled when THIS selected sample is the active sample
        # Active sample = status is 'loaded' (has no ejected_timestamp)
        self.btn_eject.setEnabled(status == 'loaded')

        # Delete only enabled for ejected samples (not active)
        self.btn_delete.setEnabled(status == 'ejected')

        # Show sample data in read-only view
        self._show_sample_readonly(filename)

        # Refresh timeline to highlight this sample's events
        self.timeline_table.repaint()

    def _show_placeholder(self):
        """Show placeholder text in form panel"""
        self.form_panel.removeAll()
        placeholder = JLabel("Select a sample or create a new one", JLabel.CENTER)
        placeholder.setFont(placeholder.getFont().deriveFont(Font.ITALIC, 12.0))
        self.form_panel.add(placeholder, BorderLayout.CENTER)
        self.form_panel.revalidate()
        self.form_panel.repaint()

        # Hide all action buttons in placeholder view
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_edit.setEnabled(False)

    def _show_sample_readonly(self, filename):
        """Show sample data in read-only HTML view"""
        if not self.current_directory:
            return

        try:
            filepath = os.path.join(self.current_directory, filename)
            data = self.sample_io.read_sample(filepath)

            # Determine which schema to use
            schema_version = data.get('metadata', {}).get('schema_version', '0.0.1')
            schema_path = self._get_schema_path_for_version(schema_version)

            if schema_path is None:
                # Schema version not found - show error in form area
                self.form_panel.removeAll()
                error_panel = self._create_schema_error_panel(schema_version)
                self.form_panel.add(error_panel, BorderLayout.CENTER)
                self.form_panel.revalidate()
                self.form_panel.repaint()
                self.update_status("Cannot display sample - schema v%s not found" % schema_version)
                return

            # Create HTML view generator
            html_generator = HTMLViewGenerator(schema_path)
            html_content = html_generator.generate_html(data)

            # Create JEditorPane to display HTML
            editor_pane = JEditorPane('text/html', html_content)
            editor_pane.setEditable(False)
            editor_pane.setCaretPosition(0)  # Reset to top

            # Clear form panel and add HTML view
            self.form_panel.removeAll()
            scroll_pane = JScrollPane(editor_pane)
            scroll_pane.getVerticalScrollBar().setUnitIncrement(16)
            scroll_pane.getVerticalScrollBar().setBlockIncrement(50)
            self.form_panel.add(scroll_pane, BorderLayout.CENTER)

            self.form_panel.revalidate()
            self.form_panel.repaint()

            # Reset scroll position to top after rendering
            from javax.swing import SwingUtilities
            SwingUtilities.invokeLater(lambda: scroll_pane.getVerticalScrollBar().setValue(0))

            # Hide Save/Cancel buttons, show Edit button in view mode
            self.btn_save.setVisible(False)
            self.btn_cancel.setVisible(False)
            self.btn_edit.setEnabled(True)

            self.update_status("Viewing sample: %s" % filename)

        except Exception as e:
            import traceback
            error_msg = "Error loading sample: %s" % str(e)
            self.update_status(error_msg)
            # Print full traceback for debugging
            traceback.print_exc()

    def _disable_form_components(self, component):
        """Recursively disable all input components in a container"""
        if hasattr(component, 'getComponents'):
            for child in component.getComponents():
                self._disable_form_components(child)

        # Disable ALL interactive components including buttons
        if isinstance(component, (JTextField, JTextArea, JComboBox, JButton)):
            if isinstance(component, JButton):
                # Disable all buttons (including Add/Remove in arrays)
                component.setEnabled(False)
            else:
                # Disable input fields
                component.setEditable(False) if hasattr(component, 'setEditable') else None
                component.setEnabled(False) if isinstance(component, JComboBox) else None

    def _load_sample_into_form(self, filename):
        """Load sample data into form"""
        if not self.current_directory:
            return

        try:
            filepath = os.path.join(self.current_directory, filename)
            data = self.sample_io.read_sample(filepath)

            # Determine which schema to use for editing
            schema_version = data.get('metadata', {}).get('schema_version', '0.0.1')
            schema_path = self._get_schema_path_for_version(schema_version)

            if schema_path is None:
                # Schema version not found - show error in form area
                self.form_panel.removeAll()
                error_panel = self._create_schema_error_panel(schema_version)
                self.form_panel.add(error_panel, BorderLayout.CENTER)
                self.form_panel.revalidate()
                self.form_panel.repaint()
                self.update_status("Cannot edit sample - schema v%s not found" % schema_version)
                return

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

            # Reset modification flag and disable Save, but enable Cancel
            self.form_modified = False
            self.btn_save.setEnabled(False)
            self.btn_cancel.setEnabled(True)  # Allow canceling edit mode

            # Show Save/Cancel buttons, hide Edit button in edit mode
            self.btn_save.setVisible(True)
            self.btn_cancel.setVisible(True)
            self.btn_edit.setEnabled(False)

            self.update_status("Loaded sample: %s (schema v%s)" % (filename, schema_version))

        except Exception as e:
            self.update_status("Error loading sample: %s" % str(e))

    def _new_sample(self):
        """Create new sample"""
        # Check if current directory matches current dataset, continue automatically if switched
        # Don't auto-select after navigation since we're creating a new sample
        if not self._check_directory_matches_curdata(callback=self._new_sample_impl, auto_select_after_nav=False):
            # User chose to switch directories - callback will handle the operation
            return

        # Proceed with creating sample in current directory
        self._new_sample_impl()

    def _new_sample_impl(self):
        """Implementation of new sample creation (after directory check)"""
        # Check if active sample exists and prompt to eject
        active = self._get_active_sample()
        if active:
            result = JOptionPane.showConfirmDialog(
                self.frame,
                "Active sample '%s' is currently loaded.\nMark as ejected and create new sample?" % active['label'],
                "Mark as Ejected",
                JOptionPane.YES_NO_OPTION,
                JOptionPane.WARNING_MESSAGE
            )
            if result != JOptionPane.YES_OPTION:
                return

            # Eject the active sample
            try:
                self.sample_io.eject_sample(active['filepath'])
                self._refresh_sample_list()
                self._refresh_timeline()
            except Exception as e:
                MSG("Error marking sample as ejected: %s" % str(e))
                return

        # Set draft state first
        self.current_sample_file = None
        self.is_draft = True
        self.draft_data = {}
        self.form_modified = False

        # Update badge and refresh sample list to show draft
        self._update_badge()
        self._refresh_sample_list()  # Refresh to show draft in list

        # Create fresh form generator using CURRENT schema for new samples
        self.form_generator = SchemaFormGenerator(self.current_schema_path)

        # Create empty form
        self.form_panel.removeAll()
        form_scroll = self.form_generator.create_form_panel(self)  # Pass app for modification tracking
        self.form_panel.add(form_scroll, BorderLayout.CENTER)
        self.form_panel.revalidate()
        self.form_panel.repaint()

        # Set button states
        self.btn_save.setEnabled(False)
        self.btn_cancel.setEnabled(True)  # Enable cancel for drafts

        # Show Save/Cancel buttons, hide Edit button when creating new
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)
        self.btn_edit.setEnabled(False)

        self.tabbed_pane.setSelectedIndex(0)  # Switch to Sample Details tab
        self.update_status("Creating new sample (draft)")

    def _duplicate_sample(self):
        """Duplicate selected sample"""
        if not self.current_sample_file:
            self.update_status("Please select a sample to duplicate")
            return

        # Read the sample data BEFORE directory check (so we have it if directory changes)
        try:
            filepath = os.path.join(self.current_directory, self.current_sample_file)
            sample_data = self.sample_io.read_sample(filepath)
        except Exception as e:
            MSG("Error reading sample: %s" % str(e))
            return

        # Store data for callback to use
        self._duplicate_data = sample_data

        # Check if current directory matches current dataset, continue automatically if switched
        # Don't auto-select after navigation since we're creating a duplicate (draft)
        if not self._check_directory_matches_curdata(callback=self._duplicate_sample_impl, auto_select_after_nav=False):
            # User chose to switch directories - callback will handle the operation
            return

        # Proceed with duplicating sample in current directory
        self._duplicate_sample_impl()

    def _duplicate_sample_impl(self):
        """Implementation of sample duplication (after directory check)"""
        # Retrieve the sample data (stored before directory check)
        data = getattr(self, '_duplicate_data', None)
        if data is None:
            MSG("Error: sample data not available")
            return

        # Clean up stored data
        delattr(self, '_duplicate_data')

        # Check if active sample exists and prompt to eject
        active = self._get_active_sample()
        if active:
            result = JOptionPane.showConfirmDialog(
                self.frame,
                "Active sample '%s' is currently loaded.\nMark as ejected and duplicate selected sample?" % active['label'],
                "Mark as Ejected",
                JOptionPane.YES_NO_OPTION,
                JOptionPane.WARNING_MESSAGE
            )
            if result != JOptionPane.YES_OPTION:
                return

            # Eject the active sample
            try:
                self.sample_io.eject_sample(active['filepath'])
                self._refresh_sample_list()
                self._refresh_timeline()
            except Exception as e:
                MSG("Error marking sample as ejected: %s" % str(e))
                return

        try:

            # Append "(copy)" to label
            if 'sample' in data and 'label' in data['sample']:
                data['sample']['label'] = data['sample']['label'] + " (copy)"

            # Remove metadata timestamps - will be regenerated with current schema
            if 'metadata' in data:
                data['metadata'].pop('created_timestamp', None)
                data['metadata'].pop('modified_timestamp', None)
                data['metadata'].pop('ejected_timestamp', None)
                data['metadata'].pop('schema_version', None)

            # Set draft state first
            self.current_sample_file = None
            self.is_draft = True
            self.draft_data = data
            self.form_modified = False

            # Update badge and refresh sample list to show draft
            self._update_badge()
            self._refresh_sample_list()  # Refresh to show draft in list

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

            # Set button states
            self.btn_save.setEnabled(False)
            self.btn_cancel.setEnabled(True)  # Enable cancel for drafts

            # Show Save/Cancel buttons, hide Edit button when duplicating
            self.btn_save.setVisible(True)
            self.btn_cancel.setVisible(True)
            self.btn_edit.setEnabled(False)

            self.tabbed_pane.setSelectedIndex(0)  # Switch to Sample Details tab
            self.update_status("Duplicating sample (draft)")

        except Exception as e:
            self.update_status("Error duplicating sample: %s" % str(e))

    def _edit_sample(self):
        """Edit selected sample"""
        if not self.current_sample_file:
            MSG("Please select a sample to edit")
            return

        # Check if this is the active sample and warn
        active = self._get_active_sample()
        if active and active['filename'] == self.current_sample_file:
            result = JOptionPane.showConfirmDialog(
                self.frame,
                "This sample is currently loaded in the spectrometer.\nEdit anyway?",
                "Active Sample Warning",
                JOptionPane.YES_NO_OPTION,
                JOptionPane.WARNING_MESSAGE
            )
            if result != JOptionPane.YES_OPTION:
                return

        self._load_sample_into_form(self.current_sample_file)
        self.is_draft = False  # Editing existing sample, not a draft
        self._update_badge()
        self.tabbed_pane.setSelectedIndex(0)  # Switch to Sample Details tab

    def _eject_active_sample(self):
        """Eject the currently active sample (virtual - timestamp only)"""
        active = self._get_active_sample()
        if not active:
            MSG("No active sample to eject")
            return

        # Confirm ejection
        result = JOptionPane.showConfirmDialog(
            self.frame,
            "Mark '%s' as ejected?" % active['label'],
            "Mark as Ejected",
            JOptionPane.YES_NO_OPTION,
            JOptionPane.QUESTION_MESSAGE
        )
        if result != JOptionPane.YES_OPTION:
            return

        try:
            self.sample_io.eject_sample(active['filepath'])
            self._refresh_sample_list()
            self._refresh_timeline()
            self._update_badge()
            self.update_status("Marked as ejected: %s" % active['label'])
        except Exception as e:
            MSG("Error marking sample as ejected: %s" % str(e))

    def _delete_sample(self):
        """Delete the selected sample (must be ejected, not active)"""
        if not self.current_sample_file:
            MSG("Please select a sample to delete")
            return

        selected_row = self.sample_table.getSelectedRow()
        if selected_row < 0:
            return

        row_data = self.sample_table_model.get_row(selected_row)
        status = row_data['status']
        label = row_data['label']

        # Can't delete active samples
        if status == 'loaded':
            MSG("Cannot delete active sample.\nPlease eject it first.")
            return

        # Confirm deletion
        result = JOptionPane.showConfirmDialog(
            self.frame,
            "Permanently delete '%s'?\nThis cannot be undone." % label,
            "Confirm Deletion",
            JOptionPane.YES_NO_OPTION,
            JOptionPane.WARNING_MESSAGE
        )
        if result != JOptionPane.YES_OPTION:
            return

        try:
            filepath = os.path.join(self.current_directory, self.current_sample_file)
            os.remove(filepath)
            self._refresh_sample_list()
            self._refresh_timeline()
            self._show_placeholder()
            self.current_sample_file = None
            self.selected_sample_filepath = None
            self.update_status("Deleted sample: %s" % label)
        except Exception as e:
            MSG("Error deleting sample: %s" % str(e))

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
                sample_label = data.get('sample', {}).get('label', 'Sample')
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
                    if 'metadata' in existing_data:
                        if 'metadata' not in data:
                            data['metadata'] = {}
                        # Preserve creation timestamp and ejection timestamp
                        data['metadata']['created_timestamp'] = existing_data['metadata'].get('created_timestamp')
                        if 'ejected_timestamp' in existing_data['metadata']:
                            data['metadata']['ejected_timestamp'] = existing_data['metadata'].get('ejected_timestamp')
                except:
                    pass  # If we can't read existing, proceed without preserved metadata

            filepath = os.path.join(self.current_directory, filename)

            # Write sample
            self.sample_io.write_sample(filepath, data, is_new=is_new)

            # Clear draft state BEFORE refreshing list
            self.is_draft = False
            self.draft_data = None

            self._refresh_sample_list()
            self._refresh_timeline()

            # Reset modification flag and disable buttons
            self.form_modified = False
            self.btn_save.setEnabled(False)
            self.btn_cancel.setEnabled(False)

            # Update badge
            self._update_badge()

            # Update current sample file reference and re-select in table
            self.current_sample_file = filename

            # Find and select this sample in the table
            for row_idx in range(self.sample_table_model.getRowCount()):
                row_data = self.sample_table_model.get_row(row_idx)
                if row_data['filename'] == filename:
                    self.sample_table.setRowSelectionInterval(row_idx, row_idx)
                    # Force reload in read-only view
                    self._on_sample_selected()
                    break

            self.update_status("Saved sample: %s" % filename)

        except Exception as e:
            MSG("Error saving sample: %s" % str(e))

    def _show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.frame, self.config)
        dialog.setLocationRelativeTo(self.frame)
        dialog.setVisible(True)

    def _cancel_edit(self):
        """Cancel current edit"""
        # If form was modified or is draft, confirm cancellation
        if self.form_modified or self.is_draft:
            result = JOptionPane.showConfirmDialog(
                self.frame,
                "You have unsaved changes. Discard them?",
                "Discard Changes",
                JOptionPane.YES_NO_OPTION,
                JOptionPane.WARNING_MESSAGE
            )
            if result != JOptionPane.YES_OPTION:  # User clicked No or closed dialog
                return

        # Remember which sample we were viewing (before clearing state)
        sample_to_reload = self.current_sample_file if not self.is_draft else None

        # Clear all edit state FIRST (before refreshing list)
        self.is_draft = False
        self.draft_data = None
        self.form_modified = False
        self.btn_save.setEnabled(False)
        self.btn_cancel.setEnabled(False)

        # Update badge and refresh sample list (removes draft if it was showing)
        self._update_badge()
        self._refresh_sample_list()

        # Reload the sample in read-only view if we were editing an existing sample
        if sample_to_reload:
            # Re-select the row in the table which will trigger _on_sample_selected
            # This will properly reload it in read-only view
            for row_idx in range(self.sample_table_model.getRowCount()):
                row_data = self.sample_table_model.get_row(row_idx)
                if row_data['filename'] == sample_to_reload:
                    self.sample_table.setRowSelectionInterval(row_idx, row_idx)
                    # Force the selection event to fire
                    self._on_sample_selected()
                    break
        else:
            self.current_sample_file = None
            self._show_placeholder()

        self.update_status("Cancelled")

    def _on_tab_changed(self):
        """Handle tab change - refresh catalogue when Samples tab is opened"""
        if self.tabbed_pane.getSelectedIndex() == 2:  # Samples tab (index 2)
            self._refresh_catalogue()
            # If a sample is selected, find and select it in the catalogue
            if self.selected_sample_filepath:
                self._select_sample_in_catalogue(self.selected_sample_filepath)

    def _refresh_catalogue(self):
        """Refresh the sample catalogue"""
        if not self.catalogue_table_model:
            return

        # Get search roots
        roots = self.config.get_search_roots()

        if not roots:
            # Show empty state
            self.catalogue_table_model.clear_rows()
            if self.catalogue_center_panel:
                card_layout = self.catalogue_center_panel.getLayout()
                card_layout.show(self.catalogue_center_panel, "EMPTY")
            self.update_status("No search directories configured. Use Settings to add directories.")
            return

        # Show table view
        if self.catalogue_center_panel:
            card_layout = self.catalogue_center_panel.getLayout()
            card_layout.show(self.catalogue_center_panel, "TABLE")

        self.update_status("Scanning directories for samples...")

        # Scan directories for samples
        try:
            samples = self.sample_scanner.scan_roots(roots)
            self.catalogue_table_model.set_rows(samples)
            self.update_status("Found %d samples in %d directories" % (len(samples), len(roots)))
        except Exception as e:
            self.update_status("Error scanning directories: %s" % str(e))

    def _select_sample_in_catalogue(self, filepath):
        """Select a sample in the catalogue table by filepath

        Args:
            filepath: Full path to sample file
        """
        if not self.catalogue_table_model:
            return

        # Find the sample in the catalogue rows
        for idx in range(self.catalogue_table_model.getRowCount()):
            row_data = self.catalogue_table_model.get_row(idx)
            if row_data and row_data.get('filepath') == filepath:
                # Found it - select the row (accounting for sorting)
                try:
                    view_idx = self.catalogue_table.convertRowIndexToView(idx)
                    self.catalogue_table.setRowSelectionInterval(view_idx, view_idx)
                    self.catalogue_table.scrollRectToVisible(
                        self.catalogue_table.getCellRect(view_idx, 0, True)
                    )
                except:
                    # If conversion fails, just select by model index
                    self.catalogue_table.setRowSelectionInterval(idx, idx)
                    self.catalogue_table.scrollRectToVisible(
                        self.catalogue_table.getCellRect(idx, 0, True)
                    )
                break

    def handle_catalogue_double_click(self, sample_info):
        """Handle double-click on catalogue entry - navigate to sample location

        Args:
            sample_info: Dictionary with sample information including 'directory' and 'filename'
        """
        directory = sample_info.get('directory')
        filename = sample_info.get('filename')

        if directory and filename:
            # Navigate to the directory
            self.set_directory(directory, auto_select=False)

            # Find and select the sample in the list
            sample_files = self.sample_io.list_sample_files(directory)
            for idx, f in enumerate(sample_files):
                if f == filename:
                    self.sample_table.setRowSelectionInterval(idx, idx)
                    self.sample_table.scrollRectToVisible(
                        self.sample_table.getCellRect(idx, 0, True)
                    )
                    # Switch to Sample Details tab
                    self.tabbed_pane.setSelectedIndex(0)
                    break

    def _on_catalogue_selection_changed(self):
        """Handle selection change in catalogue table - enable/disable buttons"""
        if not self.catalogue_table or not self.catalogue_btn_view:
            return

        has_selection = self.catalogue_table.getSelectedRow() >= 0

        if self.catalogue_btn_view:
            self.catalogue_btn_view.setEnabled(has_selection)
        if self.catalogue_btn_edit:
            self.catalogue_btn_edit.setEnabled(has_selection)
        if self.catalogue_btn_duplicate:
            self.catalogue_btn_duplicate.setEnabled(has_selection)

    def _get_selected_catalogue_row_data(self):
        """Get the data for the currently selected catalogue row"""
        if not self.catalogue_table:
            return None

        selected_row = self.catalogue_table.getSelectedRow()
        if selected_row < 0:
            return None

        # Convert to model row in case table is sorted
        model_row = self.catalogue_table.convertRowIndexToModel(selected_row)
        return self.catalogue_table_model.get_row(model_row)

    def _catalogue_view_selected(self):
        """View button handler - navigate to selected sample"""
        row_data = self._get_selected_catalogue_row_data()
        if row_data:
            self.handle_catalogue_double_click(row_data)

    def _catalogue_edit_selected(self):
        """Edit button handler - navigate to selected sample and enter edit mode"""
        row_data = self._get_selected_catalogue_row_data()
        if not row_data:
            return

        directory = row_data.get('directory')
        filename = row_data.get('filename')

        if directory and filename:
            # Navigate to the directory
            self.set_directory(directory, auto_select=False)

            # Find and select the sample in the list
            sample_files = self.sample_io.list_sample_files(directory)
            for idx, f in enumerate(sample_files):
                if f == filename:
                    self.current_sample_file = filename
                    self.sample_table.setRowSelectionInterval(idx, idx)
                    # Trigger edit mode
                    self._edit_sample()
                    # Switch to Sample Details tab
                    self.tabbed_pane.setSelectedIndex(0)
                    break

    def _catalogue_duplicate_selected(self):
        """Duplicate button handler - duplicate selected sample into current directory"""
        row_data = self._get_selected_catalogue_row_data()
        if not row_data:
            return

        filepath = row_data.get('filepath')
        if not filepath:
            return

        # Check if we have a current directory
        if not self.current_directory:
            MSG("Please navigate to a directory first")
            return

        try:
            # Read the sample data
            data = self.sample_io.read_sample(filepath)

            # Append "(copy)" to label
            if 'Sample' in data and 'Label' in data['Sample']:
                data['Sample']['Label'] = data['Sample']['Label'] + " (copy)"

            # Remove metadata timestamps - will be regenerated with current schema
            if 'Metadata' in data:
                data['Metadata'].pop('created_timestamp', None)
                data['Metadata'].pop('modified_timestamp', None)
                data['Metadata'].pop('ejected_timestamp', None)
                data['Metadata'].pop('schema_version', None)

            # Check if active sample exists and prompt to eject
            active = self._get_active_sample()
            if active:
                result = JOptionPane.showConfirmDialog(
                    self.frame,
                    "Active sample '%s' is currently loaded.\nEject it and duplicate selected sample?" % active['label'],
                    "Eject Active Sample",
                    JOptionPane.YES_NO_OPTION,
                    JOptionPane.WARNING_MESSAGE
                )
                if result != JOptionPane.YES_OPTION:
                    return

                # Eject the active sample
                self.sample_io.eject_sample(active['filepath'])
                self._refresh_sample_list()
                self._refresh_timeline()

            # Set draft state
            self.current_sample_file = None
            self.is_draft = True
            self.draft_data = data
            self.form_modified = False

            # Update badge and refresh sample list to show draft
            self._update_badge()
            self._refresh_sample_list()

            # Create fresh form generator using CURRENT schema for duplicates
            self.form_generator = SchemaFormGenerator(self.current_schema_path)

            # Create form first
            self.form_panel.removeAll()
            form_scroll = self.form_generator.create_form_panel(self)
            self.form_panel.add(form_scroll, BorderLayout.CENTER)

            # Then load data
            self.form_generator.load_data(data)

            self.form_panel.revalidate()
            self.form_panel.repaint()

            # Set button states
            self.btn_new.setEnabled(True)
            self.btn_duplicate.setEnabled(False)
            self.btn_edit.setEnabled(False)
            self.btn_eject.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.btn_save.setEnabled(False)
            self.btn_cancel.setEnabled(True)

            # Show Save/Cancel buttons, hide Edit button when duplicating from catalogue
            self.btn_save.setVisible(True)
            self.btn_cancel.setVisible(True)
            self.btn_edit.setEnabled(False)

            # Switch to Sample Details tab
            self.tabbed_pane.setSelectedIndex(0)

            self.update_status("Sample duplicated - edit and save to create new sample")

        except Exception as e:
            MSG("Error duplicating sample: %s" % str(e))

    def _refresh_timeline(self):
        """Refresh timeline view"""
        if not self.current_directory:
            self.timeline_table_model.clear_rows()
            return

        try:
            entries = self.timeline_builder.build_timeline(self.current_directory)

            # Check if we need a holder column (any non-zero holder values or multiple different holders)
            holder_values = set()
            for entry in entries:
                if entry.entry_type == 'experiment' and entry.holder is not None:
                    holder_values.add(entry.holder)

            # Show holder column if we have multiple different values or any non-zero values
            show_holder = len(holder_values) > 1 or (len(holder_values) == 1 and 0 not in holder_values)

            # Check if we have any sample events
            has_samples = any(entry.entry_type in ('sample_created', 'sample_ejected') for entry in entries)

            rows = []
            current_sample_filepath = None
            current_holder = None
            current_sample_color_index = 0  # Track color index for alternating
            sample_was_ejected = False
            current_sample_created_time = None
            current_sample_ejected_time = None

            for entry in entries:
                toggle = False

                # Check if we need to toggle due to previous ejection
                if sample_was_ejected:
                    toggle = True
                    sample_was_ejected = False

                # Convert UTC timestamp to local time for display
                import calendar
                import time
                # Convert datetime to timestamp, then to local time
                utc_timestamp = calendar.timegm(entry.timestamp.timetuple())
                local_dt = datetime.fromtimestamp(utc_timestamp)

                # Format timestamp for display - capitalize, no zero padding
                # Manual formatting for cross-platform compatibility
                day_name = local_dt.strftime("%a")  # Mon, Tue, etc.
                day = local_dt.day  # 1-31, no zero padding
                month = local_dt.strftime("%b")  # Jan, Feb, etc.
                year = local_dt.year
                hour = local_dt.hour
                minute = local_dt.minute

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

                # Determine display name and sample filepath for this row
                row_sample_filepath = current_sample_filepath
                is_orphan = False

                if entry.entry_type == 'sample_created':
                    display_name = entry.name
                    # Toggle if different sample
                    if current_sample_filepath != entry.filepath:
                        toggle = True
                    row_sample_filepath = entry.filepath
                    current_sample_filepath = entry.filepath
                    current_sample_created_time = entry.timestamp
                    current_sample_ejected_time = None
                elif entry.entry_type == 'sample_ejected':
                    display_name = "sample ejected"
                    # Ejection event uses current sample colour for this row
                    row_sample_filepath = current_sample_filepath
                    current_sample_ejected_time = entry.timestamp
                    # Set flag so next row gets new colour
                    sample_was_ejected = True
                    current_sample_filepath = None
                elif entry.entry_type == 'experiment':
                    # Detect orphaned experiments (only if we have samples defined)
                    if has_samples:
                        # Experiment is orphaned if:
                        # 1. No current sample is active (between samples or before first sample)
                        if current_sample_filepath is None:
                            is_orphan = True
                        # 2. Current sample exists but experiment is before its creation time
                        elif current_sample_created_time and entry.timestamp < current_sample_created_time:
                            is_orphan = True
                        # 3. Current sample has been ejected and experiment is after ejection
                        # (This shouldn't happen because we set current_sample_filepath = None on ejection,
                        # but check anyway for safety)
                        elif current_sample_ejected_time and entry.timestamp > current_sample_ejected_time:
                            is_orphan = True

                    # Add warning text for orphaned experiments
                    if is_orphan:
                        display_name = "Exp %s (no associated sample)" % entry.name
                    else:
                        display_name = "Exp %s" % entry.name

                    # If no samples defined, use holder for color alternation
                    if not has_samples and show_holder and entry.holder is not None:
                        if current_holder != entry.holder:
                            toggle = True
                            current_holder = entry.holder
                else:
                    display_name = entry.name

                # Apply toggle after all decision logic
                if toggle:
                    current_sample_color_index = 1 - current_sample_color_index


                # Extract just pulse program name from details (no nuclei, no scans)
                details = entry.details
                if details and ',' in details:
                    details = details.split(',')[0].strip()  # Just the pulse program

                # Get holder value (only for experiments)
                holder_str = ""
                if entry.entry_type == 'experiment' and entry.holder is not None:
                    holder_str = str(entry.holder)

                rows.append({
                    'timestamp': timestamp_str,
                    'name': display_name,
                    'holder': holder_str,
                    'details': details,
                    'entry': entry,
                    'sample_filepath': row_sample_filepath,  # For highlighting
                    'color_index': current_sample_color_index,  # For consistent coloring
                    'parmod': entry.parmod if entry.entry_type == 'experiment' else None,  # For dimensionality coloring
                    'is_orphan': is_orphan  # Flag orphaned experiments
                })

            self.timeline_table_model.set_rows(rows, show_holder)

            # Configure column widths after structure changes
            col_model = self.timeline_table.getColumnModel()
            col_model.getColumn(0).setPreferredWidth(220)  # Date/Time
            col_model.getColumn(1).setPreferredWidth(180)  # Sample/Experiment

            if show_holder:
                col_model.getColumn(2).setPreferredWidth(60)   # Holder
                col_model.getColumn(3).setPreferredWidth(250)  # Details
            else:
                col_model.getColumn(2).setPreferredWidth(250)  # Details

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

    def _validate_timeline_selection_for_sample(self):
        """
        Validate timeline selection for creating a retrospective sample.
        Returns True if selection is valid:
        - Contiguous experiments only (no sample events)
        - No experiments belonging to existing samples
        """
        selected_rows = self.timeline_table.getSelectedRows()

        # Need at least one row selected
        if len(selected_rows) == 0:
            return False

        # Check if all selected rows are experiments (not sample events)
        # Also check that none belong to existing samples
        model = self.timeline_table.getModel()
        for row in selected_rows:
            row_data = model.get_row(row)
            if not row_data or 'entry' not in row_data:
                return False
            entry = row_data['entry']
            if entry.entry_type != 'experiment':
                return False
            # Check if this experiment belongs to an existing sample
            if row_data.get('sample_filepath'):
                return False

        # Check if rows are contiguous
        sorted_rows = sorted(selected_rows)
        for i in range(len(sorted_rows) - 1):
            if sorted_rows[i+1] - sorted_rows[i] != 1:
                return False

        return True

    def _update_timeline_selection_state(self):
        """Update button states based on timeline selection"""
        if self.create_from_selection_btn:
            can_create = self._validate_timeline_selection_for_sample()
            self.create_from_selection_btn.setEnabled(can_create)

        # Update reassignment buttons
        can_reassign_prev, can_reassign_next = self._can_reassign_experiments()
        if self.reassign_prev_btn:
            self.reassign_prev_btn.setEnabled(can_reassign_prev)
        if self.reassign_next_btn:
            self.reassign_next_btn.setEnabled(can_reassign_next)

        if self.view_sample_btn:
            can_view = self._can_view_sample_from_timeline()
            self.view_sample_btn.setEnabled(can_view)

        if self.open_experiment_btn:
            can_open = self._can_open_experiment_from_timeline()
            self.open_experiment_btn.setEnabled(can_open)

    def _can_view_sample_from_timeline(self):
        """Check if we can view/edit a sample (selection includes experiment belonging to a sample)"""
        selected_rows = self.timeline_table.getSelectedRows()
        if len(selected_rows) != 1:
            return False

        model = self.timeline_table.getModel()
        row_data = model.get_row(selected_rows[0])
        if not row_data:
            return False

        # Can view if this row has an associated sample
        return row_data.get('sample_filepath') is not None

    def _can_open_experiment_from_timeline(self):
        """Check if we can open an experiment (single experiment row selected)"""
        selected_rows = self.timeline_table.getSelectedRows()
        if len(selected_rows) != 1:
            return False

        model = self.timeline_table.getModel()
        row_data = model.get_row(selected_rows[0])
        if not row_data or 'entry' not in row_data:
            return False

        entry = row_data['entry']
        return entry.entry_type == 'experiment'

    def _view_sample_from_timeline(self):
        """View/edit the sample associated with the selected experiment"""
        if not self._can_view_sample_from_timeline():
            return

        selected_rows = self.timeline_table.getSelectedRows()
        model = self.timeline_table.getModel()
        row_data = model.get_row(selected_rows[0])

        sample_filepath = row_data.get('sample_filepath')
        if not sample_filepath:
            return

        # Find this sample in the sample table and select it
        filename = os.path.basename(sample_filepath)
        sample_files = self.sample_io.list_sample_files(self.current_directory)

        for idx, fname in enumerate(sample_files):
            if fname == filename:
                self.sample_table.setRowSelectionInterval(idx, idx)
                self.sample_table.scrollRectToVisible(
                    self.sample_table.getCellRect(idx, 0, True)
                )
                # Switch to Sample Details tab
                self.tabbed_pane.setSelectedIndex(0)
                # Edit the sample
                self._edit_sample()
                break

    def _open_experiment_from_timeline(self):
        """Open the selected experiment in TopSpin"""
        if not self._can_open_experiment_from_timeline():
            return

        selected_rows = self.timeline_table.getSelectedRows()
        model = self.timeline_table.getModel()
        row_data = model.get_row(selected_rows[0])

        if row_data and 'entry' in row_data:
            entry = row_data['entry']
            self.handle_timeline_double_click(entry)

    def _create_sample_from_experiments(self):
        """Create a retrospective sample from selected experiments"""
        # Validate selection
        if not self._validate_timeline_selection_for_sample():
            MSG("Please select contiguous experiment rows (no sample events)")
            return

        # Get selected experiments
        selected_rows = sorted(self.timeline_table.getSelectedRows())
        model = self.timeline_table.getModel()

        experiments = []
        for row in selected_rows:
            row_data = model.get_row(row)
            if row_data and 'entry' in row_data:
                experiments.append(row_data['entry'])

        if len(experiments) == 0:
            MSG("No experiments selected")
            return

        # Get timestamps of first and last experiments
        first_exp = experiments[0]
        last_exp = experiments[-1]

        # Add a few seconds before/after for safety
        created_time = first_exp.timestamp - timedelta(seconds=5)
        ejected_time = last_exp.timestamp + timedelta(seconds=5)

        # Format timestamps as ISO 8601 in UTC
        created_timestamp = created_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        ejected_timestamp = ejected_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        # Look for the most recent sample before the selection to offer duplication
        previous_sample_data = None
        previous_sample_label = None
        first_selected_row = selected_rows[0]
        for row in range(first_selected_row - 1, -1, -1):
            row_data = model.get_row(row)
            if row_data and 'entry' in row_data:
                entry = row_data['entry']
                if entry.entry_type in ('sample_created', 'sample_ejected'):
                    filepath = row_data.get('sample_filepath')
                    if filepath:
                        try:
                            previous_sample_data = self.sample_io.read_sample(filepath)
                            previous_sample_label = previous_sample_data.get('sample', {}).get('label', '') or 'previous sample'
                        except Exception:
                            pass
                    break

        # Prompt: new sample or duplicate previous?
        if previous_sample_data is not None:
            options = ["New sample", "Duplicate '%s'" % previous_sample_label, "Cancel"]
            choice = JOptionPane.showOptionDialog(
                self.frame,
                "Create a new blank sample, or duplicate '%s'?" % previous_sample_label,
                "Create Sample from Experiments",
                JOptionPane.DEFAULT_OPTION,
                JOptionPane.QUESTION_MESSAGE,
                None,
                options,
                options[0]
            )
            if choice == 2 or choice == JOptionPane.CLOSED_OPTION:
                return
            use_duplicate = (choice == 1)
        else:
            use_duplicate = False

        # Build sample data
        try:
            # Load schema to get version
            schema_version = '0.1.0'  # Default version
            try:
                with open(self.current_schema_path, 'r') as f:
                    schema = json.load(f)
                    schema_version = schema.get('version', '0.1.0')
            except:
                pass  # Use default if can't read schema

            if use_duplicate:
                # Base on previous sample, stripping timestamps
                sample_data = previous_sample_data
                if 'sample' in sample_data and 'label' in sample_data['sample']:
                    sample_data['sample']['label'] = sample_data['sample']['label'] + " (copy)"
                sample_data.setdefault('metadata', {})
            else:
                # Blank sample
                sample_data = {
                    'sample': {'label': ''},
                    'buffer': {},
                    'nmr_tube': {},
                    'laboratory_reference': {},
                    'metadata': {},
                    'users': [],
                    'notes': ''
                }

            # Set metadata timestamps
            sample_data['metadata']['schema_version'] = schema_version
            sample_data['metadata']['created_timestamp'] = created_timestamp
            sample_data['metadata']['modified_timestamp'] = created_timestamp
            sample_data['metadata']['ejected_timestamp'] = ejected_timestamp

            # Create a descriptive filename based on first experiment timestamp
            filename = self.sample_io.generate_filename('retrospective', timestamp=created_time)
            filepath = os.path.join(self.current_directory, filename)

            # Save the sample (it's already ejected, so no auto-eject logic)
            self.sample_io.write_sample(filepath, sample_data)

            # Refresh views
            self._refresh_sample_list()
            self._refresh_timeline()
            self._refresh_catalogue()

            # Select the new sample in the list and open for editing
            sample_files = self.sample_io.list_sample_files(self.current_directory)
            for idx, fname in enumerate(sample_files):
                if fname == filename:
                    self.sample_table.setRowSelectionInterval(idx, idx)
                    self.sample_table.scrollRectToVisible(
                        self.sample_table.getCellRect(idx, 0, True)
                    )
                    # Switch to Sample Details tab and edit
                    self.tabbed_pane.setSelectedIndex(0)
                    self._edit_sample()
                    break

            self.update_status("Created retrospective sample for %d experiments" % len(experiments))

        except Exception as e:
            MSG("Error creating sample: %s" % str(e))
            self.update_status("Error creating sample")

    def _can_reassign_experiments(self):
        """
        Check if reassignment actions are available for selected experiments.
        Returns (can_reassign_prev, can_reassign_next) tuple of booleans.
        """
        selected_rows = self.timeline_table.getSelectedRows()
        if len(selected_rows) == 0:
            return (False, False)

        model = self.timeline_table.getModel()

        # Check if ALL selected rows are orphaned experiments
        all_orphans = True
        for row in selected_rows:
            row_data = model.get_row(row)
            if not row_data or 'entry' not in row_data:
                return (False, False)
            entry = row_data['entry']
            if entry.entry_type != 'experiment':
                return (False, False)
            if not row_data.get('is_orphan', False):
                all_orphans = False
                break

        if not all_orphans:
            return (False, False)

        # Get all timeline rows to find adjacent samples
        all_rows = []
        for i in range(model.getRowCount()):
            all_rows.append(model.get_row(i))

        # Find the first and last selected row indices in full timeline
        first_selected = min(selected_rows)
        last_selected = max(selected_rows)

        # Check for previous sample (before first selected)
        # We want to find a sample that was ejected before these orphaned experiments
        can_reassign_prev = False
        for i in range(first_selected - 1, -1, -1):
            row_data = all_rows[i]
            if row_data and 'entry' in row_data:
                entry = row_data['entry']
                if entry.entry_type == 'sample_ejected':
                    # Found an ejected sample - we can extend its ejection time
                    can_reassign_prev = True
                    break
                elif entry.entry_type == 'sample_created':
                    # Found a sample creation with no ejection - still active, not a previous sample
                    break

        # Check for next sample (after last selected)
        can_reassign_next = False
        for i in range(last_selected + 1, len(all_rows)):
            row_data = all_rows[i]
            if row_data and 'entry' in row_data:
                entry = row_data['entry']
                if entry.entry_type == 'sample_created':
                    can_reassign_next = True
                    break

        return (can_reassign_prev, can_reassign_next)

    def _reassign_to_previous_sample(self):
        """Reassign selected orphaned experiments to the previous sample"""
        selected_rows = self.timeline_table.getSelectedRows()
        if len(selected_rows) == 0:
            return

        model = self.timeline_table.getModel()

        # Get the experiments being reassigned
        experiments = []
        for row in sorted(selected_rows):
            row_data = model.get_row(row)
            if row_data and 'entry' in row_data:
                experiments.append(row_data['entry'])

        if len(experiments) == 0:
            return

        # Find the previous sample (most recent ejection before selected experiments)
        first_selected = min(selected_rows)
        last_selected = max(selected_rows)
        previous_sample_entry = None
        previous_sample_filepath = None

        all_rows = []
        for i in range(model.getRowCount()):
            all_rows.append(model.get_row(i))

        for i in range(first_selected - 1, -1, -1):
            row_data = all_rows[i]
            if row_data and 'entry' in row_data:
                entry = row_data['entry']
                if entry.entry_type == 'sample_ejected':
                    previous_sample_entry = entry
                    previous_sample_filepath = entry.filepath
                    break
                elif entry.entry_type == 'sample_created':
                    break

        if not previous_sample_filepath:
            JOptionPane.showMessageDialog(
                self.frame,
                "Could not find previous sample",
                "Reassignment Error",
                JOptionPane.ERROR_MESSAGE
            )
            return

        # Get sample label for confirmation
        try:
            sample_data = self.sample_io.read_sample(previous_sample_filepath)
            sample_label = sample_data.get('sample', {}).get('label', 'Unknown')
        except:
            sample_label = 'Unknown'

        # Get timestamp based on the LAST SELECTED experiment
        last_exp_time = experiments[-1].timestamp + timedelta(seconds=5)

        # Find orphaned experiments that will be affected by this timestamp change
        # Only experiments UP TO AND INCLUDING the selection will be affected
        affected_experiments = []
        for i in range(first_selected, last_selected + 1):
            row_data = all_rows[i]
            if row_data and 'entry' in row_data:
                entry = row_data['entry']
                if entry.entry_type == 'experiment' and row_data.get('is_orphan', False):
                    affected_experiments.append(entry.name)

        # Show confirmation dialog
        if len(affected_experiments) > len(experiments):
            exp_list = ", ".join(affected_experiments)
            message = ("Reassign experiments %s to sample '%s'?\n\n" +
                       "Selected: %s\n" +
                       "Additional experiments that will be included: %s\n\n" +
                       "The sample's ejection timestamp will be updated to %s") % (
                exp_list, sample_label,
                ", ".join([e.name for e in experiments]),
                ", ".join([e for e in affected_experiments if e not in [exp.name for exp in experiments]]),
                last_exp_time.strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            exp_list = ", ".join([e.name for e in experiments])
            message = ("Reassign experiments %s to sample '%s'?\n\n" +
                       "The sample's ejection timestamp will be updated to %s") % (
                exp_list, sample_label, last_exp_time.strftime("%Y-%m-%d %H:%M:%S")
            )

        result = JOptionPane.showConfirmDialog(
            self.frame,
            message,
            "Confirm Reassignment",
            JOptionPane.OK_CANCEL_OPTION,
            JOptionPane.QUESTION_MESSAGE
        )

        if result != JOptionPane.OK_OPTION:
            return

        # Update the sample's ejected timestamp
        try:
            sample_data = self.sample_io.read_sample(previous_sample_filepath)
            ejected_timestamp = last_exp_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            sample_data['metadata']['ejected_timestamp'] = ejected_timestamp
            sample_data['metadata']['modified_timestamp'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

            self.sample_io.write_sample(previous_sample_filepath, sample_data)

            # Refresh views
            self._refresh_sample_list()
            self._refresh_timeline()
            self._refresh_catalogue()

            self.update_status("Reassigned %d experiments to previous sample" % len(experiments))

        except Exception as e:
            JOptionPane.showMessageDialog(
                self.frame,
                "Error updating sample: %s" % str(e),
                "Reassignment Error",
                JOptionPane.ERROR_MESSAGE
            )

    def _reassign_to_next_sample(self):
        """Reassign selected orphaned experiments to the next sample"""
        selected_rows = self.timeline_table.getSelectedRows()
        if len(selected_rows) == 0:
            return

        model = self.timeline_table.getModel()

        # Get the experiments being reassigned
        experiments = []
        for row in sorted(selected_rows):
            row_data = model.get_row(row)
            if row_data and 'entry' in row_data:
                experiments.append(row_data['entry'])

        if len(experiments) == 0:
            return

        # Find the next sample
        first_selected = min(selected_rows)
        last_selected = max(selected_rows)
        next_sample_entry = None
        next_sample_filepath = None

        all_rows = []
        for i in range(model.getRowCount()):
            all_rows.append(model.get_row(i))

        for i in range(last_selected + 1, len(all_rows)):
            row_data = all_rows[i]
            if row_data and 'entry' in row_data:
                entry = row_data['entry']
                if entry.entry_type == 'sample_created':
                    next_sample_entry = entry
                    next_sample_filepath = entry.filepath
                    break

        if not next_sample_filepath:
            JOptionPane.showMessageDialog(
                self.frame,
                "Could not find next sample",
                "Reassignment Error",
                JOptionPane.ERROR_MESSAGE
            )
            return

        # Get sample label for confirmation
        try:
            sample_data = self.sample_io.read_sample(next_sample_filepath)
            sample_label = sample_data.get('sample', {}).get('label', 'Unknown')
        except:
            sample_label = 'Unknown'

        # Get timestamp of first experiment
        first_exp_time = experiments[0].timestamp - timedelta(seconds=5)

        # Find ALL orphaned experiments before the next sample that will be affected
        affected_experiments = []
        for i in range(first_selected, last_selected + 1):
            row_data = all_rows[i]
            if row_data and 'entry' in row_data:
                entry = row_data['entry']
                if entry.entry_type == 'experiment' and row_data.get('is_orphan', False):
                    affected_experiments.append(entry.name)

        # Also check for experiments between last selected and the next sample
        for i in range(last_selected + 1, len(all_rows)):
            row_data = all_rows[i]
            if row_data and 'entry' in row_data:
                entry = row_data['entry']
                if entry.entry_type == 'sample_created':
                    break
                elif entry.entry_type == 'experiment' and row_data.get('is_orphan', False):
                    affected_experiments.append(entry.name)

        # Show confirmation dialog
        if len(affected_experiments) > len(experiments):
            exp_list = ", ".join(affected_experiments)
            message = ("Reassign experiments %s to sample '%s'?\n\n" +
                       "Selected: %s\n" +
                       "Additional experiments that will be included: %s\n\n" +
                       "The sample's creation timestamp will be updated to %s") % (
                exp_list, sample_label,
                ", ".join([e.name for e in experiments]),
                ", ".join([e for e in affected_experiments if e not in [exp.name for exp in experiments]]),
                first_exp_time.strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            exp_list = ", ".join([e.name for e in experiments])
            message = ("Reassign experiments %s to sample '%s'?\n\n" +
                       "The sample's creation timestamp will be updated to %s") % (
                exp_list, sample_label, first_exp_time.strftime("%Y-%m-%d %H:%M:%S")
            )

        result = JOptionPane.showConfirmDialog(
            self.frame,
            message,
            "Confirm Reassignment",
            JOptionPane.OK_CANCEL_OPTION,
            JOptionPane.QUESTION_MESSAGE
        )

        if result != JOptionPane.OK_OPTION:
            return

        # Update the sample's created timestamp
        try:
            sample_data = self.sample_io.read_sample(next_sample_filepath)
            created_timestamp = first_exp_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            sample_data['metadata']['created_timestamp'] = created_timestamp
            sample_data['metadata']['modified_timestamp'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

            self.sample_io.write_sample(next_sample_filepath, sample_data)

            # Refresh views
            self._refresh_sample_list()
            self._refresh_timeline()
            self._refresh_catalogue()

            self.update_status("Reassigned %d experiments to next sample" % len(experiments))

        except Exception as e:
            JOptionPane.showMessageDialog(
                self.frame,
                "Error updating sample: %s" % str(e),
                "Reassignment Error",
                JOptionPane.ERROR_MESSAGE
            )

    def _reassign_to_new_sample(self):
        """Create a new sample for the selected orphaned experiments"""
        selected_rows = self.timeline_table.getSelectedRows()
        if len(selected_rows) == 0:
            return

        model = self.timeline_table.getModel()

        # Get the experiments being reassigned
        experiments = []
        for row in sorted(selected_rows):
            row_data = model.get_row(row)
            if row_data and 'entry' in row_data:
                experiments.append(row_data['entry'])

        if len(experiments) == 0:
            return

        # Get timestamps of first and last experiments
        first_exp = experiments[0]
        last_exp = experiments[-1]

        # Add a few seconds before/after for safety
        created_time = first_exp.timestamp - timedelta(seconds=5)
        ejected_time = last_exp.timestamp + timedelta(seconds=5)

        # Show confirmation dialog
        exp_list = ", ".join([e.name for e in experiments])
        message = ("Create a new sample for experiments %s?\n\n" +
                   "Sample creation time: %s\n" +
                   "Sample ejection time: %s\n\n" +
                   "You will be able to edit the sample details after creation.") % (
            exp_list,
            created_time.strftime("%Y-%m-%d %H:%M:%S"),
            ejected_time.strftime("%Y-%m-%d %H:%M:%S")
        )

        result = JOptionPane.showConfirmDialog(
            self.frame,
            message,
            "Confirm New Sample",
            JOptionPane.OK_CANCEL_OPTION,
            JOptionPane.QUESTION_MESSAGE
        )

        if result != JOptionPane.OK_OPTION:
            return

        # Create the sample (same logic as _create_sample_from_experiments)
        try:
            # Format timestamps as ISO 8601 in UTC
            created_timestamp = created_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            ejected_timestamp = ejected_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            # Load schema to get version
            schema_version = '0.1.0'  # Default version
            try:
                with open(self.current_schema_path, 'r') as f:
                    schema = json.load(f)
                    schema_version = schema.get('version', '0.1.0')
            except:
                pass  # Use default if can't read schema

            # Create default sample data
            sample_data = {
                'sample': {'label': ''},
                'buffer': {},
                'nmr_tube': {},
                'laboratory_reference': {},
                'metadata': {
                    'schema_version': schema_version,
                    'created_timestamp': created_timestamp,
                    'modified_timestamp': created_timestamp,
                    'ejected_timestamp': ejected_timestamp
                },
                'users': [],
                'notes': ''
            }

            # Create a descriptive filename based on first experiment timestamp
            filename = self.sample_io.generate_filename('reassigned', timestamp=created_time)
            filepath = os.path.join(self.current_directory, filename)

            # Save the sample
            self.sample_io.write_sample(filepath, sample_data)

            # Refresh views
            self._refresh_sample_list()
            self._refresh_timeline()
            self._refresh_catalogue()

            # Select the new sample in the list and open for editing
            sample_files = self.sample_io.list_sample_files(self.current_directory)
            for idx, fname in enumerate(sample_files):
                if fname == filename:
                    self.sample_table.setRowSelectionInterval(idx, idx)
                    self.sample_table.scrollRectToVisible(
                        self.sample_table.getCellRect(idx, 0, True)
                    )
                    # Switch to Sample Details tab and edit
                    self.tabbed_pane.setSelectedIndex(0)
                    self._edit_sample()
                    break

            self.update_status("Created new sample for %d experiments" % len(experiments))

        except Exception as e:
            JOptionPane.showMessageDialog(
                self.frame,
                "Error creating sample: %s" % str(e),
                "Reassignment Error",
                JOptionPane.ERROR_MESSAGE
            )

    def update_status(self, text):
        """Update status label"""
        self.status_label.setText(text)

    def _check_updates_background(self):
        """Check for updates in a background thread to avoid blocking UI"""
        import threading

        def check_and_update():
            has_updates, error_msg, debug_info = self._check_for_updates()
            # Update UI on the Event Dispatch Thread
            SwingUtilities.invokeLater(lambda: self._update_update_indicator(has_updates, error_msg, debug_info))

        thread = threading.Thread(target=check_and_update)
        thread.daemon = True
        thread.start()

    def show(self):
        """Show the window if hidden"""
        if self.frame is not None:
            self.frame.setVisible(True)
            self.frame.toFront()
            self.frame.requestFocus()
            # Check for updates in background
            self._check_updates_background()

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
                elif status == 'draft':
                    component.setText(u"\u25CF")  # Filled circle
                    component.setForeground(Color(218, 165, 32))  # Amber/gold
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
        self.show_holder = False
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
            if self.show_holder:
                return row_data['holder']
            else:
                return row_data['details']
        elif col == 3:
            return row_data['details']
        return None

    def get_row(self, row):
        """Get full row data"""
        if row >= 0 and row < len(self.rows):
            return self.rows[row]
        return None

    def set_rows(self, rows, show_holder=False):
        """Replace all rows and set column visibility"""
        self.rows = rows
        self.show_holder = show_holder

        # Update column names based on whether holder is shown
        if show_holder:
            self.column_names = ['Date/Time', 'Sample/Experiment', 'Holder', 'Details']
        else:
            self.column_names = ['Date/Time', 'Sample/Experiment', 'Details']

        self.fireTableStructureChanged()

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
            is_orphan = row_data.get('is_orphan', False)

            # Highlight orphaned experiments with warning color (highest priority)
            if is_orphan:
                component.setBackground(Color(255, 235, 205))  # Peach/light orange warning
            # Highlight rows matching selected sample (softer yellow)
            elif self.app.selected_sample_filepath and sample_filepath == self.app.selected_sample_filepath:
                component.setBackground(Color(255, 252, 230))  # Soft pale yellow
            else:
                # Alternate colors by sample using color_index
                if color_index == 0:
                    component.setBackground(self.color_white)
                else:
                    component.setBackground(self.color_grey)

        # Color pulse programs by dimensionality in Details column
        # Use PARMOD from row data: dimensions = parmod + 1
        # Details is column 2 when holder is hidden, column 3 when holder is shown
        model = table.getModel()
        details_column = 3 if model.show_holder else 2

        if column == details_column and value and not isSelected:
            # Get parmod from row data to determine dimensionality
            parmod = row_data.get('parmod') if row_data else None

            if parmod is not None:
                dimensions = parmod + 1
                # Color by dimensionality
                if dimensions >= 3:
                    # 3D+ experiments (green)
                    component.setForeground(Color(0, 128, 0))
                elif dimensions == 2:
                    # 2D experiments (blue)
                    component.setForeground(Color(0, 0, 200))
                else:
                    # 1D experiments (black)
                    component.setForeground(Color.BLACK)
            else:
                # No parmod data - default to black
                component.setForeground(Color.BLACK)
        elif not isSelected:
            component.setForeground(Color.BLACK)

        return component


class BadgeClickListener(MouseAdapter):
    """Mouse listener for badge clicks - navigate to active sample"""

    def __init__(self, app):
        self.app = app

    def mouseClicked(self, event):
        """Handle click on badge"""
        # Navigate to active sample in the list
        active = self.app._get_active_sample()
        if active:
            # Find this sample in the table and select it
            sample_files = self.app.sample_io.list_sample_files(self.app.current_directory)
            for idx, filename in enumerate(sample_files):
                if filename == active['filename']:
                    self.app.sample_table.setRowSelectionInterval(idx, idx)
                    # Scroll to make it visible
                    self.app.sample_table.scrollRectToVisible(
                        self.app.sample_table.getCellRect(idx, 0, True)
                    )
                    # Switch to Sample Details tab
                    self.app.tabbed_pane.setSelectedIndex(0)
                    break


class SampleTableMouseListener(MouseAdapter):
    """Mouse listener for sample table (double-click and right-click context menu)"""

    def __init__(self, app):
        self.app = app

    def mouseClicked(self, event):
        """Handle double-click to edit"""
        if event.getClickCount() == 2:
            # Get the selected row
            table = event.getSource()
            row = table.getSelectedRow()
            if row >= 0:
                row_data = table.getModel().get_row(row)
                # Don't try to edit drafts (they're already in edit mode)
                if row_data and not row_data.get('is_draft', False):
                    self.app._edit_sample()

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

            # Get row data to determine enabled states
            row_data = None
            if row >= 0:
                row_data = table.getModel().get_row(row)

            # Create context menu
            popup = JPopupMenu()

            # New - always enabled
            item_new = JMenuItem("New...")
            item_new.addActionListener(lambda e: self.app._new_sample())
            popup.add(item_new)

            if row >= 0 and row_data and not row_data.get('is_draft', False):
                popup.addSeparator()

                # Duplicate - enabled when sample is selected
                item_duplicate = JMenuItem("Duplicate...")
                item_duplicate.addActionListener(lambda e: self.app._duplicate_sample())
                popup.add(item_duplicate)

                # Edit - enabled when sample is selected
                item_edit = JMenuItem("Edit")
                item_edit.addActionListener(lambda e: self.app._edit_sample())
                popup.add(item_edit)

                popup.addSeparator()

                # Mark as ejected - only enabled for loaded (active) samples
                status = row_data.get('status', '')
                item_eject = JMenuItem("Mark as ejected")
                item_eject.setEnabled(status == 'loaded')
                item_eject.addActionListener(lambda e: self.app._eject_active_sample())
                popup.add(item_eject)

                # Delete - only enabled for ejected samples
                item_delete = JMenuItem("Delete")
                item_delete.setEnabled(status == 'ejected')
                item_delete.addActionListener(lambda e: self.app._delete_sample())
                popup.add(item_delete)

            popup.show(event.getComponent(), event.getX(), event.getY())


class TimelineMouseListener(MouseAdapter):
    """Mouse listener for timeline double-clicks and context menu"""

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

    def mousePressed(self, event):
        self._handle_popup(event)

    def mouseReleased(self, event):
        self._handle_popup(event)

    def _handle_popup(self, event):
        if event.isPopupTrigger():
            table = event.getSource()
            row = table.rowAtPoint(event.getPoint())

            # Select row if not already selected (if clicking on a row)
            if row >= 0:
                selected_rows = table.getSelectedRows()
                if row not in selected_rows:
                    table.setRowSelectionInterval(row, row)

            # Create context menu
            popup = JPopupMenu()

            # Get validation states for different actions
            can_create_retrospective = self.app._validate_timeline_selection_for_sample()
            can_view_sample = self.app._can_view_sample_from_timeline()
            can_open_experiment = self.app._can_open_experiment_from_timeline()

            # Check if reassignment actions are available
            can_reassign_prev, can_reassign_next = self.app._can_reassign_experiments()

            # Create sample from selection - enabled when valid selection
            item_create = JMenuItem("Create sample from selection")
            item_create.setEnabled(can_create_retrospective)
            item_create.addActionListener(lambda e: self.app._create_sample_from_experiments())
            popup.add(item_create)

            popup.addSeparator()

            # Reassignment options - always visible for discoverability, conditionally enabled
            # Reassign to previous sample
            item_reassign_prev = JMenuItem("Reassign experiments to previous sample")
            item_reassign_prev.setEnabled(can_reassign_prev)
            item_reassign_prev.addActionListener(lambda e: self.app._reassign_to_previous_sample())
            popup.add(item_reassign_prev)

            # Reassign to next sample
            item_reassign_next = JMenuItem("Reassign experiments to next sample")
            item_reassign_next.setEnabled(can_reassign_next)
            item_reassign_next.addActionListener(lambda e: self.app._reassign_to_next_sample())
            popup.add(item_reassign_next)

            # # Reassign to new sample
            # item_reassign_new = JMenuItem("Create new sample for experiments")
            # item_reassign_new.setEnabled(can_reassign_prev or can_reassign_next)
            # item_reassign_new.addActionListener(lambda e: self.app._reassign_to_new_sample())
            # popup.add(item_reassign_new)

            popup.addSeparator()

            # View/Edit Sample - enabled when experiment belonging to sample is selected
            item_view = JMenuItem("View/edit sample")
            item_view.setEnabled(can_view_sample)
            item_view.addActionListener(lambda e: self.app._view_sample_from_timeline())
            popup.add(item_view)

            # Open Experiment - enabled when experiment is selected
            item_open = JMenuItem("Open experiment in Topspin")
            item_open.setEnabled(can_open_experiment)
            item_open.addActionListener(lambda e: self.app._open_experiment_from_timeline())
            popup.add(item_open)

            popup.show(event.getComponent(), event.getX(), event.getY())


class CancelAction(AbstractAction):
    """Action to handle Escape key for cancelling form edits"""

    def __init__(self, app):
        AbstractAction.__init__(self)
        self.app = app

    def actionPerformed(self, event):
        self.app._cancel_edit()


class CatalogueTableModel(AbstractTableModel):
    """Table model for sample catalogue"""

    def __init__(self):
        self.rows = []
        self.all_rows = []  # Store all rows for filtering
        self.column_names = ['Created', 'Experiment', 'Label', 'Components', 'Buffer', 'Tube', 'Notes', 'Users']

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
            # Format timestamp - date only, convert UTC to local time
            created = row_data.get('created', '')
            if created:
                try:
                    import calendar
                    # Parse UTC timestamp
                    dt_utc = datetime.strptime(created[:19], "%Y-%m-%dT%H:%M:%S")
                    # Convert to local time
                    utc_timestamp = calendar.timegm(dt_utc.timetuple())
                    dt_local = datetime.fromtimestamp(utc_timestamp)
                    return dt_local.strftime("%Y-%m-%d")
                except:
                    return created[:10]
            return ''
        elif col == 1:
            return row_data.get('experiment', '')
        elif col == 2:
            return row_data.get('label', '')
        elif col == 3:
            return row_data.get('components', '')
        elif col == 4:
            return row_data.get('buffer', '')
        elif col == 5:
            return row_data.get('tube', '')
        elif col == 6:
            return row_data.get('notes', '')
        elif col == 7:
            return row_data.get('users', '')
        return None

    def get_row(self, row):
        """Get full row data"""
        if row >= 0 and row < len(self.rows):
            return self.rows[row]
        return None

    def set_rows(self, rows):
        """Replace all rows"""
        self.all_rows = rows
        self.rows = rows
        self.fireTableDataChanged()

    def filter_rows(self, search_text):
        """Filter rows based on search text (supports comma-separated terms)"""
        if not search_text:
            self.rows = self.all_rows
        else:
            # Split by comma and strip whitespace from each term
            search_terms = [term.strip().lower() for term in search_text.split(',') if term.strip()]

            self.rows = []
            for row in self.all_rows:
                # Search across all text fields
                searchable = ' '.join([
                    str(row.get('created', '')),
                    str(row.get('experiment', '')),
                    str(row.get('label', '')),
                    str(row.get('users', '')),
                    str(row.get('components', '')),
                    str(row.get('buffer', '')),
                    str(row.get('tube', '')),
                    str(row.get('notes', ''))
                ]).lower()

                # Match if ALL terms are found (AND logic)
                if all(term in searchable for term in search_terms):
                    self.rows.append(row)

        self.fireTableDataChanged()

    def clear_rows(self):
        """Clear all rows"""
        self.rows = []
        self.all_rows = []
        self.fireTableDataChanged()


class CatalogueTableCellRenderer(DefaultTableCellRenderer):
    """Custom cell renderer for catalogue table with tooltips"""

    def getTableCellRendererComponent(self, table, value, isSelected, hasFocus, row, column):
        component = DefaultTableCellRenderer.getTableCellRendererComponent(
            self, table, value, isSelected, hasFocus, row, column)

        # Get actual row in model (in case table is sorted)
        model_row = table.convertRowIndexToModel(row)
        model = table.getModel()
        row_data = model.get_row(model_row)

        if row_data:
            # Set tooltips based on column
            col_name = model.getColumnName(column)

            if col_name == 'Label':
                tooltip = row_data.get('label_tooltip', '')
                if tooltip:
                    component.setToolTipText("<html>%s</html>" % tooltip.replace('\n', '<br>'))
                else:
                    component.setToolTipText(None)

            elif col_name == 'Components':
                tooltip = row_data.get('components_tooltip', '')
                if tooltip:
                    component.setToolTipText("<html>%s</html>" % tooltip.replace('\n', '<br>'))
                else:
                    component.setToolTipText(None)

            elif col_name == 'Buffer':
                tooltip = row_data.get('buffer_tooltip', '')
                if tooltip:
                    component.setToolTipText("<html>%s</html>" % tooltip.replace('\n', '<br>'))
                else:
                    component.setToolTipText(None)

            elif col_name == 'Tube':
                tooltip = row_data.get('tube_tooltip', '')
                if tooltip:
                    component.setToolTipText("<html>%s</html>" % tooltip.replace('\n', '<br>'))
                else:
                    component.setToolTipText(None)

            elif col_name == 'Notes':
                tooltip = row_data.get('notes_tooltip', '')
                if tooltip:
                    # Escape HTML and preserve newlines
                    component.setToolTipText("<html>%s</html>" % tooltip.replace('\n', '<br>'))
                else:
                    component.setToolTipText(None)

            elif col_name == 'Users':
                tooltip = row_data.get('users_tooltip', '')
                if tooltip:
                    component.setToolTipText("<html>%s</html>" % tooltip.replace('\n', '<br>'))
                else:
                    component.setToolTipText(None)

            elif col_name == 'Experiment':
                tooltip = row_data.get('experiment_tooltip', '')
                if tooltip:
                    component.setToolTipText(tooltip)
                else:
                    component.setToolTipText(None)

            else:
                component.setToolTipText(None)

        return component


class CatalogueSearchListener(DocumentListener):
    """Document listener for catalogue search field"""

    def __init__(self, app):
        self.app = app

    def insertUpdate(self, event):
        self._update_filter()

    def removeUpdate(self, event):
        self._update_filter()

    def changedUpdate(self, event):
        self._update_filter()

    def _update_filter(self):
        """Apply search filter"""
        if self.app.catalogue_table_model and self.app.catalogue_search_field:
            search_text = self.app.catalogue_search_field.getText().strip()
            self.app.catalogue_table_model.filter_rows(search_text)


class CatalogueMouseListener(MouseAdapter):
    """Mouse listener for catalogue double-clicks and context menu"""

    def __init__(self, app):
        self.app = app

    def mouseClicked(self, event):
        if event.getClickCount() == 2:
            table = event.getSource()
            row = table.rowAtPoint(event.getPoint())
            if row >= 0:
                # Get actual row in model (in case table is sorted)
                model_row = table.convertRowIndexToModel(row)
                row_data = table.getModel().get_row(model_row)
                if row_data:
                    self.app.handle_catalogue_double_click(row_data)

    def mousePressed(self, event):
        self._handle_popup(event)

    def mouseReleased(self, event):
        self._handle_popup(event)

    def _handle_popup(self, event):
        """Handle right-click context menu"""
        if event.isPopupTrigger():
            table = event.getSource()
            row = table.rowAtPoint(event.getPoint())

            # Select row if not already selected
            if row >= 0 and row != table.getSelectedRow():
                table.setRowSelectionInterval(row, row)

            if row >= 0:
                # Get row data
                model_row = table.convertRowIndexToModel(row)
                row_data = table.getModel().get_row(model_row)

                if row_data:
                    # Create context menu
                    popup = JPopupMenu()

                    item_view = JMenuItem("View", actionPerformed=lambda e: self._view_sample(row_data))
                    popup.add(item_view)

                    item_edit = JMenuItem("Edit", actionPerformed=lambda e: self._edit_sample(row_data))
                    popup.add(item_edit)

                    item_duplicate = JMenuItem("Duplicate into current experiment", actionPerformed=lambda e: self._duplicate_sample(row_data))
                    popup.add(item_duplicate)

                    popup.show(event.getComponent(), event.getX(), event.getY())

    def _view_sample(self, sample_info):
        """Navigate to sample and view it (read-only)"""
        self.app.handle_catalogue_double_click(sample_info)

    def _edit_sample(self, sample_info):
        """Navigate to sample and edit it"""
        # First navigate to the sample
        directory = sample_info.get('directory')
        filename = sample_info.get('filename')

        if directory and filename:
            # Navigate to the directory
            self.app.set_directory(directory, auto_select=False)

            # Find and select the sample in the list
            sample_files = self.app.sample_io.list_sample_files(directory)
            for idx, f in enumerate(sample_files):
                if f == filename:
                    self.app.current_sample_file = filename
                    self.app.sample_table.setRowSelectionInterval(idx, idx)
                    # Trigger edit mode
                    self.app._edit_sample()
                    break

    def _duplicate_sample(self, sample_info):
        """Duplicate sample into current directory"""
        # Load the sample data from its original location
        filepath = sample_info.get('filepath')
        if not filepath:
            return

        # Check if we have a current directory
        if not self.app.current_directory:
            MSG("Please navigate to a directory first")
            return

        try:
            # Read the sample data
            data = self.app.sample_io.read_sample(filepath)

            # Append "(copy)" to label
            if 'sample' in data and 'label' in data['sample']:
                data['sample']['label'] = data['sample']['label'] + " (copy)"

            # Remove metadata timestamps - will be regenerated with current schema
            if 'metadata' in data:
                data['metadata'].pop('created_timestamp', None)
                data['metadata'].pop('modified_timestamp', None)
                data['metadata'].pop('ejected_timestamp', None)
                data['metadata'].pop('schema_version', None)

            # Check if active sample exists and prompt to eject
            active = self.app._get_active_sample()
            if active:
                result = JOptionPane.showConfirmDialog(
                    self.app.frame,
                    "Active sample '%s' is currently loaded.\nMark as ejected and duplicate selected sample?" % active['label'],
                    "Mark as Ejected",
                    JOptionPane.YES_NO_OPTION,
                    JOptionPane.WARNING_MESSAGE
                )
                if result != JOptionPane.YES_OPTION:
                    return

                # Eject the active sample
                self.app.sample_io.eject_sample(active['filepath'])
                self.app._refresh_sample_list()
                self.app._refresh_timeline()

            # Set draft state
            self.app.current_sample_file = None
            self.app.is_draft = True
            self.app.draft_data = data
            self.app.form_modified = False

            # Update badge and refresh sample list to show draft
            self.app._update_badge()
            self.app._refresh_sample_list()

            # Create fresh form generator using CURRENT schema for duplicates
            self.app.form_generator = SchemaFormGenerator(self.app.current_schema_path)

            # Create form first
            self.app.form_panel.removeAll()
            form_scroll = self.app.form_generator.create_form_panel(self.app)
            self.app.form_panel.add(form_scroll, BorderLayout.CENTER)

            # Then load data
            self.app.form_generator.load_data(data)

            self.app.form_panel.revalidate()
            self.app.form_panel.repaint()

            # Set button states
            self.app.btn_save.setEnabled(False)
            self.app.btn_cancel.setEnabled(True)

            self.app.tabbed_pane.setSelectedIndex(0)  # Switch to Sample Details tab
            self.app.update_status("Duplicating sample into current directory (draft)")

        except Exception as e:
            MSG("Error duplicating sample: %s" % str(e))


class SettingsDialog(JDialog):
    """Settings dialog for configuring search directories"""

    def __init__(self, parent, config):
        JDialog.__init__(self, parent, "Settings", True)
        self.config = config
        self.setSize(600, 400)

        # Store initial state for cancel functionality
        self.initial_roots = list(config.get_search_roots())

        # Main container
        container = self.getContentPane()
        container.setLayout(BorderLayout(10, 10))

        # Title panel
        title_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        title_label = JLabel("Search Root Directories")
        title_label.setFont(title_label.getFont().deriveFont(Font.BOLD, 14.0))
        title_panel.add(title_label)
        container.add(title_panel, BorderLayout.NORTH)

        # Center panel - directory list
        center_panel = JPanel(BorderLayout(5, 5))
        center_panel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10))

        # Info label
        info_label = JLabel("<html>These directories will be searched for samples.<br>" +
                           "Subdirectories will be searched recursively.</html>")
        info_label.setFont(info_label.getFont().deriveFont(Font.PLAIN, 11.0))
        info_label.setForeground(Color(100, 100, 100))
        center_panel.add(info_label, BorderLayout.NORTH)

        # List of directories
        self.list_model = DefaultListModel()
        for root in self.initial_roots:
            self.list_model.addElement(root)

        self.directory_list = JList(self.list_model)
        self.directory_list.setSelectionMode(ListSelectionModel.SINGLE_SELECTION)
        scroll = JScrollPane(self.directory_list)
        center_panel.add(scroll, BorderLayout.CENTER)

        # Buttons to add/remove directories
        list_button_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        btn_add = JButton('Add...', actionPerformed=lambda e: self._add_directory())
        btn_remove = JButton('Remove', actionPerformed=lambda e: self._remove_directory())
        list_button_panel.add(btn_add)
        list_button_panel.add(btn_remove)
        center_panel.add(list_button_panel, BorderLayout.SOUTH)

        container.add(center_panel, BorderLayout.CENTER)

        # Bottom panel - OK/Cancel buttons
        bottom_panel = JPanel(FlowLayout(FlowLayout.RIGHT))
        bottom_panel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10))

        btn_cancel = JButton('Cancel', actionPerformed=lambda e: self._cancel())
        btn_ok = JButton('OK', actionPerformed=lambda e: self._save())
        btn_ok.setPreferredSize(Dimension(80, 28))
        btn_cancel.setPreferredSize(Dimension(80, 28))

        # Make OK button visually primary
        btn_ok.setFont(btn_ok.getFont().deriveFont(Font.BOLD))
        btn_ok.setBackground(Color(200, 230, 200))
        btn_ok.setOpaque(True)

        bottom_panel.add(btn_cancel)
        bottom_panel.add(btn_ok)

        container.add(bottom_panel, BorderLayout.SOUTH)

    def _add_directory(self):
        """Add a directory to the search roots"""
        chooser = JFileChooser()
        chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)
        chooser.setDialogTitle("Select Search Root Directory")

        if chooser.showOpenDialog(self) == JFileChooser.APPROVE_OPTION:
            path = chooser.getSelectedFile().getAbsolutePath()

            # Check if already in list
            for i in range(self.list_model.getSize()):
                if self.list_model.getElementAt(i) == path:
                    JOptionPane.showMessageDialog(
                        self,
                        "This directory is already in the list.",
                        "Duplicate Directory",
                        JOptionPane.WARNING_MESSAGE
                    )
                    return

            self.list_model.addElement(path)

    def _remove_directory(self):
        """Remove selected directory from the list"""
        selected_idx = self.directory_list.getSelectedIndex()
        if selected_idx >= 0:
            self.list_model.removeElementAt(selected_idx)
        else:
            JOptionPane.showMessageDialog(
                self,
                "Please select a directory to remove.",
                "No Selection",
                JOptionPane.INFORMATION_MESSAGE
            )

    def _save(self):
        """Save changes and close"""
        # Get all directories from list model
        roots = []
        for i in range(self.list_model.getSize()):
            roots.append(self.list_model.getElementAt(i))

        # Save to config
        self.config.set_search_roots(roots)

        self.dispose()

    def _cancel(self):
        """Cancel changes and close"""
        # Restore original roots
        self.config.set_search_roots(self.initial_roots)
        self.dispose()


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
            # Show existing instance and navigate to current dataset
            app.show()
            app._navigate_to_curdata()

    return app


def main():
    get_app()


# Run main
main()
