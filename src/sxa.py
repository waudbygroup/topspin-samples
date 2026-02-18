# -*- coding: utf-8 -*-
"""
Sample Changer Automation Command (sxa) - Automated Mode
Unified command for sample changer operations with integrated metadata management
Handles both loading specific positions (sxa XXX) and ejection (sxa ej)
"""

from java.lang import System
from javax.swing import JOptionPane
from datetime import datetime
import sys

APP_KEY = "org.nmr-samples.topspin"

# Testing mode - set to True to simulate XCMD calls with dialogs instead of actual execution
TESTING_MODE = False


def get_argument():
    """Get the sample position or command from arguments or prompt user"""
    # Check if argument was provided on command line
    if len(sys.argv) > 1:
        return sys.argv[1]

    # Prompt user for input
    result = JOptionPane.showInputDialog(
        None,
        "Enter sample changer position or 'ej' to eject:",
        "Sample Changer",
        JOptionPane.QUESTION_MESSAGE
    )

    return result


def handle_ejection(app):
    """Handle ejection workflow (sxa ej)"""
    try:
        # Get active sample state
        active = app._get_active_sample()

        # If active sample exists, confirm before ejecting
        if active:
            sample_label = active['label']
            message = "Sample '%s' will be marked as ejected. Continue?" % sample_label

            # Show confirmation dialog
            result = JOptionPane.showConfirmDialog(
                app.frame,
                message,
                "Confirm Ejection",
                JOptionPane.YES_NO_OPTION,
                JOptionPane.QUESTION_MESSAGE
            )

            if result != JOptionPane.YES_OPTION:
                return

        # Execute physical ejection
        if TESTING_MODE:
            JOptionPane.showMessageDialog(
                app.frame,
                "[TESTING MODE] Would execute: XCMD('sx ej')",
                "Testing Mode",
                JOptionPane.INFORMATION_MESSAGE
            )
        else:
            XCMD("sx ej")

        # Mark sample as ejected in metadata (if one exists)
        if active:
            app.sample_io.eject_sample(active['filepath'])
            app._refresh_sample_list()
            app._refresh_timeline()
            app._update_badge()

            # Show confirmation
            confirmation = "Sample '%s' ejected" % sample_label
            app.update_status("Sample ejected: %s" % sample_label)
            JOptionPane.showMessageDialog(
                app.frame,
                confirmation,
                "Sample Ejected",
                JOptionPane.INFORMATION_MESSAGE
            )
        # If no active sample, execute silently (no confirmation needed)

    except Exception as e:
        JOptionPane.showMessageDialog(
            None,
            "Error during ejection: %s" % str(e),
            "Error",
            JOptionPane.ERROR_MESSAGE
        )


def handle_loading(app, position):
    """Handle loading workflow (sxa XXX)"""
    try:
        # Get active sample state and check if previous samples exist
        active = app._get_active_sample()
        has_previous = app._has_previous_samples()

        # Build dialog options based on state
        if active:
            sample_label = active['label']
            message = "Sample '%s' will be marked as ejected. Loading position %s:" % (sample_label, position)

            # Options when active sample exists
            if has_previous:
                options = ["New sample", "Duplicate last sample", "Skip annotation", "Cancel"]
            else:
                options = ["New sample", "Skip annotation", "Cancel"]
        else:
            message = "Loading position %s:" % position

            # Options when no active sample
            if has_previous:
                options = ["New sample", "Duplicate last sample", "Skip annotation", "Cancel"]
            else:
                options = ["New sample", "Skip annotation", "Cancel"]

        # Show option dialog
        choice = JOptionPane.showOptionDialog(
            app.frame,
            message,
            "Load Sample",
            JOptionPane.DEFAULT_OPTION,
            JOptionPane.QUESTION_MESSAGE,
            None,
            options,
            "New sample"
        )

        # Handle Cancel
        if choice < 0 or options[choice] == "Cancel":
            return

        selected_option = options[choice]

        # Store injection timestamp before executing physical command
        injection_timestamp = datetime.utcnow()

        # Eject active sample if needed (before physical command for consistency)
        if active:
            app.sample_io.eject_sample(active['filepath'])
            app._refresh_sample_list()
            app._refresh_timeline()
            app._update_badge()

        # Execute physical loading command
        if TESTING_MODE:
            JOptionPane.showMessageDialog(
                app.frame,
                "[TESTING MODE] Would execute: XCMD('sx %s')" % position,
                "Testing Mode",
                JOptionPane.INFORMATION_MESSAGE
            )
        else:
            XCMD("sx %s" % position)

        # Process user choice - show form if needed
        if selected_option == "New sample" or selected_option == "Duplicate last sample":
            # Show the app window
            app.show()

            # Check if directory matches current dataset, offer to switch
            if not app.check_and_switch_to_curdata():
                # User declined to switch - abort operation
                JOptionPane.showMessageDialog(
                    app.frame,
                    "Sample creation cancelled - directory not switched",
                    "Cancelled",
                    JOptionPane.WARNING_MESSAGE
                )
                return

        if selected_option == "New sample":
            # Create new sample with the stored injection timestamp
            app._new_sample_with_timestamp(injection_timestamp)
            app.update_status("Loading position %s - creating new sample" % position)
        elif selected_option == "Duplicate last sample":
            # Duplicate last sample with the stored injection timestamp
            app._duplicate_last_sample_with_timestamp(injection_timestamp)
            app.update_status("Loading position %s - duplicating last sample" % position)
        # If "Skip annotation", execute silently (no confirmation needed)

    except Exception as e:
        JOptionPane.showMessageDialog(
            None,
            "Error during loading: %s" % str(e),
            "Error",
            JOptionPane.ERROR_MESSAGE
        )


def main():
    """Automated sample changer operation"""

    # Get the running application instance
    app = System.getProperties().get(APP_KEY)

    if app is None:
        JOptionPane.showMessageDialog(
            None,
            "Sample Manager not running - please start 'samples' command first",
            "Error",
            JOptionPane.ERROR_MESSAGE
        )
        return

    # Get argument (position or 'ej')
    argument = get_argument()

    if not argument:
        return  # User cancelled input dialog

    argument = argument.strip().lower()

    # Branch based on argument
    if argument == "ej":
        handle_ejection(app)
    else:
        # Assume it's a position number
        handle_loading(app, argument)


# Run main
main()
