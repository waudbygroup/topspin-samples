# -*- coding: utf-8 -*-
"""
Auto-Inject Command (aij)
Automatically inject a new sample - creates metadata and performs physical injection
"""

from java.lang import System

APP_KEY = "topspin.nmr.sample.manager"


def main():
    """Auto-inject: create new sample and perform physical injection"""

    # Get the running application instance
    app = System.getProperties().get(APP_KEY)

    if app is None:
        MSG("Sample Manager not running - please start 'samples' command first")
        return

    try:
        # Show the application window
        app.show()

        # Create new sample (this will auto-eject any active sample)
        app._new_sample()

        # Update status
        app.update_status("Ready to inject new sample")

        # TODO: Physical injection command
        # For now, show placeholder message
        MSG("Please inject sample into spectrometer")

        # Alternative: Could use TopSpin command here if available
        # XCMD("ej")  # Example - check TopSpin documentation

    except Exception as e:
        MSG("Error during auto-inject: %s" % str(e))


# Run main
main()
