# Installation Guide

This guide will walk you through installing the NMR Sample Manager in TopSpin. The process is straightforward and takes about 5 minutes.

## Prerequisites

- **Bruker TopSpin** (any recent version with Jython 2.7.2 support)
- **Git** (for cloning the repository)
- **Basic command line skills** (we'll guide you through each step)

!!! note "Installation Location"
    You **cannot** install Sample Manager within TopSpin's `/opt/topspin...` directories. You'll need to choose a location where you have write permissions, such as your home directory or a shared lab folder.

## Step 1: Choose Installation Location

First, decide where to install Sample Manager. Good options include:

```bash
# In your home directory (recommended for single-user installations)
cd ~

# Or in a shared lab directory (recommended for multi-user facilities)
cd /path/to/shared/lab/software
```

## Step 2: Clone the Repository

Clone the Sample Manager repository using git:

```bash
git clone https://github.com/waudbygroup/topspin-samples.git
```

This will create a `topspin-samples` directory containing the application.

!!! tip "What if I don't have git?"
    You can download the repository as a ZIP file from [GitHub](https://github.com/waudbygroup/topspin-samples), then unzip it in your chosen location.

## Step 3: Configure TopSpin Python Path

Now we need to tell TopSpin where to find the Sample Manager code. This is done through TopSpin's `setres` utility.

### 3.1 Configure Python Path with setres

In TopSpin, type `setres` to open the Resource Editor. Navigate to **Directories** → **Manage source directories for edpul, edau, etc.** In the popup window, select the **Jython Programs** tab and add the full path to your `topspin-samples/src` directory (e.g., `/home/username/topspin-samples/src` or `/Users/username/topspin-samples/src` on macOS). Use the full absolute path, not a relative path, and make sure to point to the `src` subdirectory.

![TopSpin setres configuration](../images/setres.png)

### 3.2 Save and Restart

1. Click **"Save"** or **"OK"** in the setres window
2. **Restart TopSpin** to apply the changes

!!! note "Why restart?"
    TopSpin only loads the Python path configuration at startup, so you need to restart for the changes to take effect.

## Step 4: Verify Installation

After restarting TopSpin, verify that Sample Manager is installed correctly:

1. In TopSpin's command line, type:
   ```
   samples
   ```

2. The Sample Manager GUI window should appear:

![Sample Manager main window](../images/sample-catalogue.png)

If you see the window, congratulations! Sample Manager is installed and ready to use.

### Troubleshooting

!!! failure "Command not found"
    If TopSpin says `samples` command is not found:

    - Check that you added the correct path to PYTHONPATH in setres
    - Make sure the path points to the `src` directory, not the parent `topspin-samples` directory
    - Verify that you restarted TopSpin after making changes
    - Check that the `samples.py` file exists in the `src` directory

!!! failure "Import errors or Python exceptions"
    If you see Python errors when running `samples`:

    - Make sure you cloned the entire repository, including the `src/lib` subdirectory
    - Check that all files in `src/` and `src/lib/` were copied correctly
    - Try cloning the repository again in case of corrupted files

!!! failure "Window appears but is blank or broken"
    If the GUI appears but looks wrong:

    - This may indicate a Java/Swing version compatibility issue
    - Check your TopSpin and Java versions
    - Report the issue on [GitHub](https://github.com/waudbygroup/topspin-samples/issues) with details about your setup

## Step 5: Updating Sample Manager

To update to the latest version of Sample Manager:

1. Open a terminal and navigate to your installation directory:
   ```bash
   cd /path/to/topspin-samples
   ```

2. Pull the latest changes from GitHub:
   ```bash
   git pull
   ```

3. Restart TopSpin to load the updated code

!!! tip "Auto-update in TopSpin"
    A future version may include an auto-update feature within the GUI. For now, manual updates via git are required.

## Next Steps

Now that Sample Manager is installed, you're ready to start using it:

- **[Quick Start Guide](quickstart.md)** - Learn the basic workflow
- **[Usage Guide](../guide/usage.md)** - Explore all features in detail

## Multi-User Installations

### Shared Lab Setup

For labs with multiple NMR users, we recommend:

1. **Install in a shared location** accessible to all users:
   ```bash
   cd /opt/lab/software  # or similar shared directory
   git clone https://github.com/waudbygroup/topspin-samples.git
   ```

2. **Each user configures their own TopSpin** by adding the shared path to PYTHONPATH via `setres`

3. **Coordinate schema updates** - when updating via `git pull`, inform all lab members to restart TopSpin

### Core Facility Setup

For NMR facilities serving multiple research groups:

1. Install Sample Manager in a central location
2. Add documentation about Sample Manager to your facility's user manual
3. Provide training sessions for new users
4. Consider creating facility-specific templates for common sample types

## Uninstallation

To remove Sample Manager:

1. Open TopSpin's `setres` utility
2. Remove the Sample Manager path from PYTHONPATH
3. Save and restart TopSpin
4. Optionally, delete the `topspin-samples` directory

!!! info "Your data is safe"
    Uninstalling Sample Manager does **not** delete your sample metadata JSON files. These remain in your NMR data directories and can still be viewed/edited using the [web-based viewer](https://github.com/waudbygroup/nmr-sample-viewer).

---

Having trouble? [Contact us](mailto:c.waudby@ucl.ac.uk) or [open an issue on GitHub](https://github.com/waudbygroup/topspin-samples/issues).
