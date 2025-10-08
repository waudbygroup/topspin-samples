# -*- coding: utf-8 -*-
"""
Schema Form Generator
Dynamically generates Swing forms from JSON Schema
"""

from javax.swing import *
from java.awt import *
import json


class SchemaFormGenerator:
    """Generate Swing form components from JSON Schema"""

    def __init__(self, schema_path):
        """Load schema from file"""
        self.schema = self._load_schema(schema_path)
        self.components = {}  # Map field paths to components
        self.data = {}  # Current form data

    @staticmethod
    def _load_schema(schema_path):
        """Load JSON schema file"""
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except (IOError, ValueError) as e:
            raise Exception("Failed to load schema: %s" % str(e))

    def create_form_panel(self):
        """Create main form panel with all fields"""
        # Clear components dictionary for fresh form
        self.components = {}

        panel = JPanel()
        panel.setLayout(BoxLayout(panel, BoxLayout.Y_AXIS))

        # Get properties from schema
        properties = self.schema.get('properties', {})

        # Create sections for each top-level property
        for prop_name in ['Users', 'Sample', 'Buffer', 'NMR Tube', 'Laboratory Reference', 'Notes']:
            if prop_name in properties:
                section_panel = self._create_section(prop_name, properties[prop_name])
                if section_panel:
                    panel.add(section_panel)
                    panel.add(Box.createVerticalStrut(10))

        return JScrollPane(panel)

    def _create_section(self, section_name, section_schema):
        """Create a collapsible section for a schema property"""
        section_panel = JPanel()
        section_panel.setLayout(BoxLayout(section_panel, BoxLayout.Y_AXIS))
        section_panel.setBorder(BorderFactory.createTitledBorder(section_name))

        prop_type = section_schema.get('type')

        if prop_type == 'array':
            # Special handling for array types (e.g., Users)
            component = self._create_array_field(section_name, section_schema)
            if component:
                section_panel.add(component)

        elif prop_type == 'object':
            # Object with properties (e.g., Sample, Buffer)
            obj_properties = section_schema.get('properties', {})
            for prop_name, prop_schema in obj_properties.items():
                field_path = "%s.%s" % (section_name, prop_name)
                component = self._create_field(field_path, prop_name, prop_schema)
                if component:
                    section_panel.add(component)
                    section_panel.add(Box.createVerticalStrut(5))

        elif prop_type == 'string':
            # Simple string field (e.g., Notes)
            component = self._create_field(section_name, section_name, section_schema)
            if component:
                section_panel.add(component)

        return section_panel

    def _create_field(self, field_path, label, field_schema):
        """Create appropriate Swing component for a field"""
        field_type = field_schema.get('type')
        enum_values = field_schema.get('enum')
        description = field_schema.get('description', '')

        field_panel = JPanel()
        field_panel.setLayout(BorderLayout())

        # Create label
        label_text = "%s:" % label
        if description:
            label_text = "%s (%s):" % (label, description)
        jlabel = JLabel(label_text)
        field_panel.add(jlabel, BorderLayout.WEST)

        # Create input component based on type
        component = None

        if enum_values:
            # Dropdown for enum values
            component = JComboBox(enum_values)
            component.setEditable(False)
        elif field_type == 'array':
            # Array field with add/remove buttons
            component = self._create_array_field(field_path, field_schema)
        elif field_type == 'number' or field_type == ['number', 'null']:
            # Number input
            component = JTextField(10)
        elif field_type == 'string' or field_type == ['string']:
            # Text input
            if label == 'Notes':
                # Multi-line for Notes
                text_area = JTextArea(4, 30)
                text_area.setLineWrap(True)
                text_area.setWrapStyleWord(True)
                component = JScrollPane(text_area)
                self.components[field_path] = text_area  # Store text area, not scroll pane
            else:
                component = JTextField(30)
        elif field_type == 'object':
            # Nested object - create sub-panel
            component = self._create_nested_object_field(field_path, field_schema)
        else:
            # Default to text field
            component = JTextField(30)

        if component and field_path not in self.components:
            self.components[field_path] = component

        if component:
            field_panel.add(component, BorderLayout.CENTER)
            return field_panel

        return None

    def _create_array_field(self, field_path, field_schema):
        """Create array field with add/remove functionality"""
        array_panel = JPanel()
        array_panel.setLayout(BoxLayout(array_panel, BoxLayout.Y_AXIS))

        items_schema = field_schema.get('items', {})
        item_type = items_schema.get('type')

        # List to hold array items
        items_list = []

        # Panel to hold item components
        items_container = JPanel()
        items_container.setLayout(BoxLayout(items_container, BoxLayout.Y_AXIS))

        def add_item():
            """Add new item to array"""
            if item_type == 'string':
                # Simple string item
                item_panel = JPanel(FlowLayout(FlowLayout.LEFT))
                text_field = JTextField(25)
                item_panel.add(text_field)

                remove_btn = JButton('Remove')
                remove_btn.addActionListener(lambda e: (items_container.remove(item_panel),
                                                        items_list.remove(text_field),
                                                        items_container.revalidate(),
                                                        items_container.repaint()))
                item_panel.add(remove_btn)

                items_container.add(item_panel)
                items_list.append(text_field)

            elif item_type == 'object':
                # Object item (e.g., Sample.Components)
                item_panel = self._create_array_object_item(field_path, items_schema, items_container, items_list)
                items_container.add(item_panel)

            items_container.revalidate()
            items_container.repaint()

        # Add button
        add_btn = JButton('Add')
        add_btn.addActionListener(lambda e: add_item())

        array_panel.add(items_container)
        array_panel.add(add_btn)

        # Store reference
        self.components[field_path] = {'container': items_container, 'items': items_list, 'schema': items_schema}

        return array_panel

    def _create_array_object_item(self, field_path, item_schema, items_container, items_list):
        """Create a single object item in an array"""
        item_panel = JPanel()
        item_panel.setLayout(BoxLayout(item_panel, BoxLayout.Y_AXIS))
        item_panel.setBorder(BorderFactory.createEtchedBorder())

        item_components = {}

        # Create fields for object properties
        item_properties = item_schema.get('properties', {})
        for prop_name, prop_schema in item_properties.items():
            prop_type = prop_schema.get('type')
            enum_values = prop_schema.get('enum')

            field_panel = JPanel(FlowLayout(FlowLayout.LEFT))
            field_panel.add(JLabel("%s:" % prop_name))

            if enum_values:
                component = JComboBox(enum_values)
            elif prop_type == 'number':
                component = JTextField(10)
            else:
                component = JTextField(15)

            item_components[prop_name] = component
            field_panel.add(component)
            item_panel.add(field_panel)

        # Remove button
        btn_panel = JPanel(FlowLayout(FlowLayout.RIGHT))
        remove_btn = JButton('Remove')
        remove_btn.addActionListener(lambda e: (items_container.remove(item_panel),
                                                items_list.remove(item_components),
                                                items_container.revalidate(),
                                                items_container.repaint()))
        btn_panel.add(remove_btn)
        item_panel.add(btn_panel)

        items_list.append(item_components)

        return item_panel

    def _create_nested_object_field(self, field_path, field_schema):
        """Create nested object (not currently used in schema, but for completeness)"""
        nested_panel = JPanel()
        nested_panel.setLayout(BoxLayout(nested_panel, BoxLayout.Y_AXIS))

        obj_properties = field_schema.get('properties', {})
        for prop_name, prop_schema in obj_properties.items():
            nested_path = "%s.%s" % (field_path, prop_name)
            component = self._create_field(nested_path, prop_name, prop_schema)
            if component:
                nested_panel.add(component)

        return nested_panel

    def load_data(self, data):
        """Load data into form components"""
        self.data = data

        for field_path, component in self.components.items():
            value = self._get_nested_value(data, field_path)

            if isinstance(component, dict):
                # Array field - populate items
                if value and isinstance(value, list):
                    self._populate_array_field(component, value)
            elif isinstance(component, JTextField):
                if value is not None:
                    component.setText(str(value))
            elif isinstance(component, JTextArea):
                if value is not None:
                    component.setText(str(value))
            elif isinstance(component, JComboBox):
                if value is not None:
                    component.setSelectedItem(value)

    def _populate_array_field(self, array_component, values):
        """Populate array field with existing data"""
        items_container = array_component.get('container')
        items_list = array_component.get('items')
        items_schema = array_component.get('schema')

        if items_container is None or items_list is None:
            return

        item_type = items_schema.get('type')

        # Clear existing items
        items_container.removeAll()
        items_list[:] = []  # Clear list in place

        # Add items from data
        for value in values:
            if item_type == 'string':
                # Simple string item
                item_panel = JPanel(FlowLayout(FlowLayout.LEFT))
                text_field = JTextField(25)
                text_field.setText(str(value))
                item_panel.add(text_field)

                remove_btn = JButton('Remove')
                remove_btn.addActionListener(lambda e, p=item_panel, t=text_field: (
                    items_container.remove(p),
                    items_list.remove(t),
                    items_container.revalidate(),
                    items_container.repaint()))
                item_panel.add(remove_btn)

                items_container.add(item_panel)
                items_list.append(text_field)

            elif item_type == 'object' and isinstance(value, dict):
                # Object item (e.g., Sample.Components)
                item_components = {}
                item_panel = JPanel()
                item_panel.setLayout(BoxLayout(item_panel, BoxLayout.Y_AXIS))
                item_panel.setBorder(BorderFactory.createEtchedBorder())

                # Create fields for object properties
                item_properties = items_schema.get('properties', {})
                for prop_name, prop_schema in item_properties.items():
                    prop_type = prop_schema.get('type')
                    enum_values = prop_schema.get('enum')

                    field_panel = JPanel(FlowLayout(FlowLayout.LEFT))
                    field_panel.add(JLabel("%s:" % prop_name))

                    if enum_values:
                        component = JComboBox(enum_values)
                        # Set selected value if exists
                        if prop_name in value:
                            component.setSelectedItem(value[prop_name])
                    elif prop_type == 'number':
                        component = JTextField(10)
                        if prop_name in value:
                            component.setText(str(value[prop_name]))
                    else:
                        component = JTextField(15)
                        if prop_name in value:
                            component.setText(str(value[prop_name]))

                    item_components[prop_name] = component
                    field_panel.add(component)
                    item_panel.add(field_panel)

                # Remove button
                btn_panel = JPanel(FlowLayout(FlowLayout.RIGHT))
                remove_btn = JButton('Remove')
                remove_btn.addActionListener(lambda e, p=item_panel, c=item_components: (
                    items_container.remove(p),
                    items_list.remove(c),
                    items_container.revalidate(),
                    items_container.repaint()))
                btn_panel.add(remove_btn)
                item_panel.add(btn_panel)

                items_container.add(item_panel)
                items_list.append(item_components)

        items_container.revalidate()
        items_container.repaint()

    def get_data(self):
        """Extract data from form components"""
        data = {}

        for field_path, component in self.components.items():
            value = None

            if isinstance(component, dict):
                # Array field
                value = self._get_array_data(component)
            elif isinstance(component, JTextField):
                text = component.getText().strip()
                if text:
                    # Try to convert to number if it looks like one
                    try:
                        if '.' in text:
                            value = float(text)
                        else:
                            value = int(text)
                    except ValueError:
                        value = text
            elif isinstance(component, JTextArea):
                text = component.getText().strip()
                if text:
                    value = text
            elif isinstance(component, JComboBox):
                value = component.getSelectedItem()

            if value is not None:
                self._set_nested_value(data, field_path, value)

        return data

    def _get_array_data(self, array_component):
        """Extract data from array field"""
        items_list = array_component.get('items', [])
        items_schema = array_component.get('schema', {})
        item_type = items_schema.get('type')

        result = []

        for item in items_list:
            if isinstance(item, JTextField):
                # Simple string item
                text = item.getText().strip()
                if text:
                    result.append(text)
            elif isinstance(item, dict):
                # Object item
                item_data = {}
                for key, comp in item.items():
                    if isinstance(comp, JTextField):
                        text = comp.getText().strip()
                        if text:
                            try:
                                item_data[key] = float(text) if '.' in text else int(text)
                            except ValueError:
                                item_data[key] = text
                    elif isinstance(comp, JComboBox):
                        item_data[key] = comp.getSelectedItem()
                if item_data:
                    result.append(item_data)

        return result if result else None

    @staticmethod
    def _get_nested_value(data, path):
        """Get value from nested dictionary using dot notation"""
        keys = path.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    @staticmethod
    def _set_nested_value(data, path, value):
        """Set value in nested dictionary using dot notation"""
        keys = path.split('.')
        current = data

        for i, key in enumerate(keys[:-1]):
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
