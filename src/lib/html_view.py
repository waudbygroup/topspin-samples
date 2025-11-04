# -*- coding: utf-8 -*-
"""
HTML View Generator
Generate styled HTML views from JSON sample data using schema information
Optimized for JEditorPane's HTML 3.2 + limited CSS support
"""

import json
from collections import OrderedDict


class HTMLViewGenerator:
    """Generate styled HTML views from JSON data using schema information"""

    def __init__(self, schema_path):
        """Load schema from file"""
        self.schema = self._load_schema(schema_path)

        # Color palette (all tested to work in JEditorPane)
        self.colors = {
            'primary': '#2c3e50',      # Dark blue-grey for headers
            'secondary': '#34495e',     # Medium grey for subheaders
            'accent': '#3498db',        # Blue for accents/borders
            'muted': '#7f8c8d',         # Grey for labels
            'background': '#f8f9fa',    # Light grey backgrounds
            'border': '#bdc3c7',        # Border color
            'warning': '#f39c12',       # Orange for important data
            'success': '#27ae60',       # Green for status
            'metadata': '#fff9e6'       # Cream for metadata sections
        }

    @staticmethod
    def _load_schema(schema_path):
        """Load JSON schema file preserving property order"""
        try:
            with open(schema_path, 'r') as f:
                return json.load(f, object_pairs_hook=OrderedDict)
        except (IOError, ValueError) as e:
            raise Exception("Failed to load schema: %s" % str(e))

    def generate_html(self, data):
        """Generate full HTML document from sample data"""
        html = self._html_header()

        # Iterate through schema properties in order
        properties = self.schema.get('properties', OrderedDict())
        for prop_name, prop_schema in properties.items():
            if prop_name in data:
                value = data[prop_name]
                # Skip empty values (None, empty string, empty dict, empty list)
                if value is None or value == '' or value == {} or value == []:
                    continue

                section_html = self._render_section(
                    prop_name,
                    prop_schema,
                    value
                )
                html += section_html

        html += self._html_footer()
        return html

    def _html_header(self):
        """Generate HTML header with CSS styles"""
        return """<html>
<head>
<style type="text/css">
body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 12px;
    margin: 10px;
    background-color: white;
}

/* Section container - two column layout */
.section-container {
    margin: 8px 0px;
    border-bottom: 1px solid %(border)s;
    padding-bottom: 8px;
}

.section-container:last-child {
    border-bottom: none;
}

/* Section header on left */
.section-header {
    color: %(primary)s;
    font-size: 12px;
    font-weight: bold;
    width: 120px;
    float: left;
    padding-top: 2px;
}

/* Section content on right */
.section-content {
    margin-left: 130px;
}

/* Subsection headers (e.g., Components) */
h3 {
    color: %(secondary)s;
    font-size: 11px;
    font-weight: bold;
    margin-top: 6px;
    margin-bottom: 3px;
}

/* Tables for arrays */
table {
    width: 100%%;
    border-collapse: collapse;
    margin: 4px 0px;
    background-color: white;
}

th {
    background-color: %(accent)s;
    color: white;
    font-weight: bold;
    padding: 4px 6px;
    text-align: left;
    font-size: 12px;
}

td {
    padding: 3px 6px;
    border-bottom: 1px solid %(border)s;
    font-size: 12px;
}

tr:last-child td {
    border-bottom: none;
}

/* Key-value pairs */
.field-row {
    margin: 2px 0px;
    padding: 0px;
}

.field-label {
    color: %(muted)s;
    font-weight: bold;
    font-size: 12px;
}

.field-value {
    color: black;
    margin-left: 8px;
    font-size: 12px;
}

/* Special sections */
.metadata-container {
    background-color: %(metadata)s;
    padding: 8px 8px 8px 0px;
    margin: 8px 0px;
    border-left: 3px solid %(warning)s;
}

.metadata-container .section-header {
    padding-left: 8px;
}

.metadata-container .section-content {
    margin-left: 130px;
}

.notes-container {
    background-color: %(background)s;
    padding: 8px 8px 8px 0px;
    margin: 8px 0px;
    border-left: 3px solid %(accent)s;
    font-style: italic;
}

.notes-container .section-header {
    padding-left: 8px;
}

.notes-container .section-content {
    margin-left: 130px;
}

/* Lists */
ul {
    margin: 3px 0px;
    padding-left: 18px;
}

li {
    margin: 1px 0px;
}

.empty-message {
    color: #999999;
    font-style: italic;
    margin-left: 8px;
    font-size: 10px;
}

/* Clear floats */
.clear {
    clear: both;
}

</style>
</head>
<body>
""" % self.colors

    def _render_section(self, prop_name, prop_schema, value):
        """Render a section based on schema type"""
        prop_type = prop_schema.get('type')
        title = prop_schema.get('title', self._format_label(prop_name))

        # Special handling for metadata - styled box
        if prop_name == 'metadata':
            return self._render_metadata_section(title, prop_schema, value)

        # Special handling for notes - styled box
        # Python 2/3 compatibility for string check
        try:
            is_string = isinstance(value, basestring)  # Python 2
        except NameError:
            is_string = isinstance(value, str)  # Python 3

        if prop_name == 'notes' and is_string:
            return self._render_notes_section(title, value)

        # Two-column layout: header on left, content on right
        html = '<div class="section-container">\n'
        html += '<div class="section-header">%s</div>\n' % self._escape_html(title)
        html += '<div class="section-content">\n'

        if prop_type == 'object':
            # Object with properties
            html += self._render_object(prop_schema, value)
        elif prop_type == 'array':
            # Array type
            items_schema = prop_schema.get('items', {})
            if items_schema.get('type') == 'string':
                # Simple string array - bullet list
                html += self._render_string_array(value)
            elif items_schema.get('type') == 'object':
                # Object array - table
                html += self._render_object_array(items_schema, value)
            else:
                # Fallback for other array types
                html += self._render_string_array(value)
        elif prop_type == 'string':
            # Simple string field
            html += '<div class="field-value">%s</div>\n' % self._escape_html(value)

        html += '</div>\n'  # Close section-content
        html += '<div class="clear"></div>\n'  # Clear float
        html += '</div>\n'  # Close section-container

        return html

    def _render_object(self, schema, data):
        """Render object as key-value pairs or nested structure"""
        html = ''
        properties = schema.get('properties', OrderedDict())

        for prop_name, prop_schema in properties.items():
            if prop_name not in data:
                continue

            value = data[prop_name]

            # Skip empty values
            if value is None or value == '' or value == {} or value == []:
                continue

            prop_type = prop_schema.get('type')
            title = prop_schema.get('title', self._format_label(prop_name))

            if prop_type == 'array':
                # Nested array (e.g., Sample.Components, Buffer.Components)
                items_schema = prop_schema.get('items', {})
                if items_schema.get('type') == 'object':
                    # Skip the h3 header for Components - table is self-explanatory
                    # Just render the table directly
                    html += self._render_object_array(items_schema, value)
                elif items_schema.get('type') == 'string':
                    html += '<div class="field-row">\n'
                    html += '<span class="field-label">%s:</span>\n' % self._escape_html(title)
                    html += '<span class="field-value">%s</span>\n' % self._escape_html(', '.join(str(v) for v in value))
                    html += '</div>\n'
                else:
                    # Fallback
                    html += '<div class="field-row">\n'
                    html += '<span class="field-label">%s:</span>\n' % self._escape_html(title)
                    html += '<span class="field-value">%s</span>\n' % self._escape_html(str(value))
                    html += '</div>\n'
            else:
                # Simple field
                html += self._render_field(title, value)

        return html

    def _render_object_array(self, items_schema, array_data):
        """Render array of objects as a table"""
        if not array_data or len(array_data) == 0:
            return '<p class="empty-message">No items</p>\n'

        properties = items_schema.get('properties', OrderedDict())

        if not properties:
            # No schema properties, just display raw data
            return '<pre>%s</pre>\n' % self._escape_html(str(array_data))

        # Build table header from schema
        html = '<table>\n<tr>\n'
        for prop_name, prop_schema in properties.items():
            title = prop_schema.get('title', self._format_label(prop_name))
            html += '<th>%s</th>' % self._escape_html(title)
        html += '</tr>\n'

        # Build table rows from data
        for item in array_data:
            if not isinstance(item, dict):
                continue

            html += '<tr>\n'
            for prop_name in properties.keys():
                value = item.get(prop_name, '')

                # Format value appropriately
                if value is None or value == '':
                    formatted_value = '<span class="empty-message">-</span>'
                elif isinstance(value, bool):
                    formatted_value = 'Yes' if value else 'No'
                elif isinstance(value, (int, float)):
                    # Format numbers nicely (remove unnecessary decimals)
                    if isinstance(value, float) and value == int(value):
                        formatted_value = str(int(value))
                    else:
                        formatted_value = str(value)
                else:
                    formatted_value = self._escape_html(str(value))

                html += '<td>%s</td>' % formatted_value
            html += '</tr>\n'

        html += '</table>\n'
        return html

    def _render_string_array(self, array_data):
        """Render string array as bullet list"""
        if not array_data or len(array_data) == 0:
            return '<p class="empty-message">None</p>\n'

        html = '<ul>\n'
        for item in array_data:
            html += '<li>%s</li>\n' % self._escape_html(str(item))
        html += '</ul>\n'
        return html

    def _render_field(self, label, value):
        """Render a simple field as key-value pair"""
        html = '<div class="field-row">\n'
        html += '<span class="field-label">%s:</span>\n' % self._escape_html(label)

        # Format value based on type
        if value is None or value == '':
            formatted_value = '<span class="empty-message">not specified</span>'
        elif isinstance(value, bool):
            formatted_value = 'Yes' if value else 'No'
        elif isinstance(value, (int, float)):
            formatted_value = str(value)
        else:
            formatted_value = self._escape_html(str(value))

        html += '<span class="field-value">%s</span>\n' % formatted_value
        html += '</div>\n'
        return html

    def _render_metadata_section(self, title, schema, data):
        """Render metadata in special styled box"""
        html = '<div class="metadata-container">\n'
        html += '<div class="section-header" style="color: %s;">%s</div>\n' % (self.colors['warning'], self._escape_html(title))
        html += '<div class="section-content">\n'

        properties = schema.get('properties', OrderedDict())
        for prop_name, prop_schema in properties.items():
            if prop_name not in data:
                continue

            value = data[prop_name]
            if value is None or value == '':
                continue

            label = prop_schema.get('title', self._format_label(prop_name))

            # Format timestamps nicely
            if 'timestamp' in prop_name and value:
                value = self._format_timestamp(value)

            html += self._render_field(label, value)

        html += '</div>\n'  # Close section-content
        html += '<div class="clear"></div>\n'  # Clear float
        html += '</div>\n'  # Close metadata-container
        return html

    def _render_notes_section(self, title, notes_text):
        """Render notes in special styled box"""
        if not notes_text or notes_text.strip() == '':
            return ''

        html = '<div class="notes-container">\n'
        html += '<div class="section-header">%s</div>\n' % self._escape_html(title)
        html += '<div class="section-content">\n'
        # Preserve line breaks in notes
        formatted_notes = self._escape_html(notes_text).replace('\n', '<br>\n')
        html += formatted_notes
        html += '</div>\n'  # Close section-content
        html += '<div class="clear"></div>\n'  # Clear float
        html += '</div>\n'  # Close notes-container
        return html

    def _format_timestamp(self, timestamp_str):
        """Format ISO timestamp to readable format"""
        try:
            from datetime import datetime
            # Handle both with and without 'Z' suffix
            if timestamp_str.endswith('Z'):
                dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            else:
                # Try parsing without milliseconds
                try:
                    dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
                except ValueError:
                    # Try with milliseconds
                    dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')

            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            # If parsing fails, return original
            return timestamp_str

    def _format_label(self, field_name):
        """Convert field_name to Title Case Label"""
        # Replace underscores with spaces and capitalize
        return ' '.join(word.capitalize() for word in field_name.split('_'))

    def _escape_html(self, text):
        """Escape HTML special characters"""
        if text is None:
            return ''
        # Python 2/3 compatibility
        try:
            # Python 2
            text_str = unicode(text) if not isinstance(text, unicode) else text
        except NameError:
            # Python 3
            text_str = str(text)
        return text_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

    def _html_footer(self):
        """Generate HTML footer"""
        return '</body>\n</html>'
