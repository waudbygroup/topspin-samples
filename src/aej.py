# -*- coding: utf-8 -*-
"""
Auto-Eject Command (aej)
Automatically eject the active sample - adds timestamp and performs physical ejection
"""

from java.lang import System

APP_KEY = "topspin.nmr.sample.manager"


def main():
    """Auto-eject: eject active sample and perform physical ejection"""

    # Get the running application instance
    app = System.getProperties().get(APP_KEY)

    if app is None:
        MSG("Sample Manager not running - please start 'samples' command first")
        return

    try:
        # Check if there's a selected sample
        if app.current_sample_file is None:
            # Try to find active sample automatically
            active_sample = app.sample_io.find_active_sample(app.current_directory)

            if active_sample:
                # Load the active sample
                app.current_sample_file = active_sample
                app._load_sample_into_form(active_sample)

                # Select it in the list
                for i in range(app.sample_list_model.size()):
                    item = app.sample_list_model.get(i)
                    if item.startswith(active_sample):
                        app.sample_list.setSelectedIndex(i)
                        break
            else:
                MSG("No active sample found to eject")
                return

        # Eject the sample (virtual - adds timestamp)
        app._eject_sample()

        # TODO: Physical ejection command
        # For now, show placeholder message
        MSG("Please eject sample from spectrometer")

        # Alternative: Could use TopSpin command here if available
        # XCMD("ej")  # Example - check TopSpin documentation

    except Exception as e:
        MSG("Error during auto-eject: %s" % str(e))


# Run main
main()
