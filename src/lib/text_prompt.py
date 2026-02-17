# -*- coding: utf-8 -*-
"""
TextPrompt - Hint text for Swing text components
Shows gray hint text that disappears when user starts typing
"""

from javax.swing.event import DocumentListener
from java.awt import Color
from java.awt.event import FocusListener, KeyAdapter


class TextPrompt(DocumentListener, FocusListener):
    """Display hint text in a text component when empty"""

    def __init__(self, text, component):
        """
        Create hint text for a text component

        Args:
            text: The hint text to display
            component: JTextField or JTextArea to attach to
        """
        self.component = component
        self.hint_text = text
        self.showing_hint = False
        self.updating = False  # Flag to prevent recursive updates

        # Store original colors
        self.hint_color = Color(160, 160, 160)
        self.normal_color = component.getForeground()

        # Add listeners
        component.addFocusListener(self)
        component.getDocument().addDocumentListener(self)

        # Add key listener to catch first keystroke
        component.addKeyListener(KeyHandler(self))

        # Show hint if empty
        if len(component.getText()) == 0:
            self.showHint()

    def showHint(self):
        """Display the hint text"""
        if not self.showing_hint and not self.updating:
            self.updating = True
            self.showing_hint = True
            self.component.setForeground(self.hint_color)
            self.component.setText(self.hint_text)
            self.updating = False

    def hideHint(self):
        """Remove the hint text"""
        if self.showing_hint and not self.updating:
            self.updating = True
            self.showing_hint = False
            self.component.setForeground(self.normal_color)
            # Only clear text if it's still the hint text
            if self.component.getText() == self.hint_text:
                self.component.setText("")
            self.updating = False

    def getText(self):
        """Get the actual text (without hint)"""
        if self.showing_hint:
            return ""
        return self.component.getText()

    # DocumentListener methods
    def insertUpdate(self, e):
        # Ignore events while we're updating
        if self.updating:
            return
        # If showing hint and text was inserted, it means user is typing
        if self.showing_hint:
            # Check if the text is different from hint (user typed something)
            from javax.swing import SwingUtilities
            SwingUtilities.invokeLater(lambda: self._checkAndHide())

    def removeUpdate(self, e):
        # Ignore events while we're updating
        if self.updating:
            return
        # If text was removed and field is now empty, show hint
        from javax.swing import SwingUtilities
        SwingUtilities.invokeLater(lambda: self._checkAndShow())

    def changedUpdate(self, e):
        pass

    def _checkAndHide(self):
        """Check if we should hide the hint"""
        if self.updating:
            return
        text = self.component.getText()
        if self.showing_hint and text != self.hint_text:
            self.hideHint()

    def _checkAndShow(self):
        """Check if we should show the hint"""
        if self.updating:
            return
        text = self.component.getText()
        if not self.showing_hint and len(text) == 0:
            self.showHint()

    # FocusListener methods
    def focusGained(self, e):
        if self.showing_hint:
            self.hideHint()

    def focusLost(self, e):
        # Don't show hint if we're in the middle of an update
        if not self.updating and len(self.component.getText()) == 0:
            self.showHint()


class KeyHandler(KeyAdapter):
    """Handle key events to clear hint on first keystroke"""

    def __init__(self, text_prompt):
        self.text_prompt = text_prompt

    def keyPressed(self, e):
        # When user starts typing, clear the hint immediately
        if self.text_prompt.showing_hint:
            self.text_prompt.hideHint()
