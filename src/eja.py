# -*- coding: utf-8 -*-
"""
Eject-and-Annotate Command (eja) - Manual Mode
Turn on lift air to raise/eject sample with integrated metadata management
"""

from java.lang import System
from javax.swing import JOptionPane

APP_KEY = "org.nmr-samples.topspin"

# Testing mode - set to True to simulate XCMD calls with dialogs instead of actual execution
TESTING_MODE = False


def main():
    """Manual eject: turn on lift air and eject sample in metadata"""

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
        # Get active sample state
        active = app._get_active_sample()

        # If active sample exists, confirm before ejecting
        if active:
            sample_label = active['label']
            message = "Sample '%s' will be marked as ejected (and lift air switched on). Continue?" % sample_label

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

        # Execute physical ejection (turn on lift air)
        if TESTING_MODE:
            JOptionPane.showMessageDialog(
                app.frame,
                "[TESTING MODE] Would execute: XCMD('ej')",
                "Testing Mode",
                JOptionPane.INFORMATION_MESSAGE
            )
        else:
            XCMD("ej")

        # Mark sample as ejected in metadata (if one exists)
        if active:
            app.sample_io.eject_sample(active['filepath'])
            app._refresh_sample_list()
            app._refresh_timeline()
            app._update_badge()

            # Show confirmation
            confirmation = "Lift air on - sample '%s' ejected" % sample_label
            app.update_status(confirmation)
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


# Run main
main()
