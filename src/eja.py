# -*- coding: utf-8 -*-
"""
Eject-and-Annotate Command (eja)
Automatically eject the active sample - adds timestamp and performs physical ejection
"""

from java.lang import System

APP_KEY = "org.waudbylab.topspin-sample-manager"


def main():
    """Auto-eject: eject active sample and perform physical ejection"""

    # Get the running application instance
    app = System.getProperties().get(APP_KEY)

    if app is None:
        MSG("Sample Manager not running - please start 'samples' command first")
        return

    try:
        # Simply call the eject method - it will find and eject the active sample
        app._eject_active_sample()

        # TODO: Physical ejection command
        # For now, show placeholder message
        MSG("Sample ejected virtually. Please eject sample from spectrometer.")

        # Alternative: Could use TopSpin command here if available
        # XCMD("ej")  # Example - check TopSpin documentation

    except Exception as e:
        MSG("Error during auto-eject: %s" % str(e))


# Run main
main()
