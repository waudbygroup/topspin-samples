# -*- coding: utf-8 -*-
"""
Inject-and-Annotate Command (ija) - Manual Mode
Turn off lift air to lower/inject sample with integrated metadata management
"""

from java.lang import System
from javax.swing import JOptionPane
from datetime import datetime

APP_KEY = "org.waudbylab.topspin-sample-manager"

# Testing mode - set to True to simulate XCMD calls with dialogs instead of actual execution
TESTING_MODE = False


def main():
    """Manual inject: turn off lift air and create/update sample metadata"""

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

    try:
        # Get active sample state and check if previous samples exist
        active = app._get_active_sample()
        has_previous = app._has_previous_samples()

        # Build dialog options based on state
        if active:
            sample_label = active['label']
            message = "Sample '%s' is active:" % sample_label

            # Options when active sample exists
            if has_previous:
                options = ["Keep Active", "Eject & Create new sample", "Eject & Duplicate last sample", "Eject & Skip annotation", "Cancel"]
                default_option = "Keep Active"
            else:
                options = ["Keep Active", "Eject & Create new sample", "Eject & Skip annotation", "Cancel"]
                default_option = "Keep Active"
        else:
            message = "Injecting sample (switching lift air off):"

            # Options when no active sample
            if has_previous:
                options = ["New sample", "Duplicate last sample", "Skip annotation", "Cancel"]
                default_option = "New sample"
            else:
                options = ["New sample", "Skip annotation", "Cancel"]
                default_option = "New sample"

        # Show option dialog
        choice = JOptionPane.showOptionDialog(
            app.frame,
            message,
            "Sample Injection",
            JOptionPane.DEFAULT_OPTION,
            JOptionPane.QUESTION_MESSAGE,
            None,
            options,
            default_option
        )

        # Handle Cancel
        if choice < 0 or options[choice] == "Cancel":
            return

        selected_option = options[choice]

        # Store injection timestamp before executing physical command
        injection_timestamp = datetime.utcnow()

        # Execute physical injection (turn off lift air)
        if TESTING_MODE:
            JOptionPane.showMessageDialog(
                app.frame,
                "[TESTING MODE] Would execute: XCMD('ij')",
                "Testing Mode",
                JOptionPane.INFORMATION_MESSAGE
            )
        else:
            XCMD("ij")

        # Process user choice
        should_eject_active = False
        should_create_new = False
        should_duplicate = False

        if selected_option == "Keep Active":
            # Do nothing - keep active sample as is
            return
        elif selected_option == "Eject & Create new sample":
            should_eject_active = True
            should_create_new = True
        elif selected_option == "Eject & Duplicate last sample":
            should_eject_active = True
            should_duplicate = True
        elif selected_option == "Eject & Skip annotation":
            should_eject_active = True
        elif selected_option == "New sample":
            should_create_new = True
        elif selected_option == "Duplicate last sample":
            should_duplicate = True
        elif selected_option == "Skip annotation":
            # Do nothing - no form
            return

        # Eject active sample if needed
        if should_eject_active and active:
            app.sample_io.eject_sample(active['filepath'])
            app._refresh_sample_list()
            app._refresh_timeline()
            app._update_badge()

        # Show the app window
        app.show()

        # Create new sample or duplicate with the stored injection timestamp
        if should_create_new:
            app._new_sample_with_timestamp(injection_timestamp)
            app.update_status("Creating new sample - lift air off")
        elif should_duplicate:
            app._duplicate_last_sample_with_timestamp(injection_timestamp)
            app.update_status("Duplicating last sample - lift air off")

    except Exception as e:
        JOptionPane.showMessageDialog(
            None,
            "Error during injection: %s" % str(e),
            "Error",
            JOptionPane.ERROR_MESSAGE
        )


# Run main
main()
