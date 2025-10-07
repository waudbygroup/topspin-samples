# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Sample manager for NMR spectroscopy

We are creating a sample management system - in this instance, to run within Bruker Topspin, but as part of a broader ecosystem
defined by a metadata schema.

## Background

NMR workflows focus on data acquisition and processing, but sample tracking has been a longstanding blind spot. Bruker software manages *experiments* effectively, but provides no systematic way to record or retrieve information about *samples* -- e.g. protein concentrations, buffer compositions, isotopic labelling schemes, chemical shift referencing, NMR tube types. This often causes problems when looking back over old data or preparing data for repository submission.

Here we describe a simple JSON schema for recording sample metadata, creating a lightweight, parallel system that captures sample information alongside TopSpin workflows.

## Data Model

- **Schema versioning**: Stored in `schemas/` with semantic versioning (referenced in sample metadata)
- **Current schema**: Symlink `schemas/current` points to active version
- **Validation**: Client-side validation using JSON Schema
- **Evolution**: Schema migrations for backwards compatibility

```json
{
  "Sample": {
    "Label": "lysozyme",
    "Components": [
      {
        "Unit": "mM",
        "Name": "HEWL",
        "Concentration": 10,
        "Isotopic labelling": "unlabelled"
      }
    ]
  },
  "Buffer": {
    "Reference unit": "%w/v",
    "pH": null,
    "Solvent": "10% D2O",
    "Chemical shift reference": "none"
  },
  "NMR Tube": {
    "Sample Volume": 600,
    "Diameter": "5 mm",
    "Type": "regular",
    "SampleJet Rack Position": "A1",
    "SampleJet Rack ID": ""
  },
  "Laboratory Reference": {
    "Labbook Entry": "",
    "Experiment ID": ""
  },
  "Metadata": {
    "schema_version": "0.0.1",
    "created_timestamp": "2023-10-09T11:10:00.000Z",
    "modified_timestamp": "2025-08-23T21:16:19.441Z",
    "ejected_timestamp": "2023-10-10T12:00:19.441Z"
  },
  "Users": [
    "Chris"
  ],
  "Notes": ""
}
```

### File Naming Convention

```
{timestamp}_{sample_name}.json
2025-08-21_143022_MyProtein.json
```


## Sample creation and ejection

- Sample files should be timestamped upon creation - this marks them as 'active'
- Samples should be timestamped upon ejection from the spectrometer - marking them as complete
- There should be no more than one active sample in a folder - creating a new sample should eject previous
- Samples can be edited and marked with a modified date distinct from the ejection time

## Ecosystem

A web-based application has been created to view and edit metadata.
Screenshots are provided in the info folder and should be examined for context.


## Architecture

### Core Design Principles

- **Standalone web application**: No servers or complex installation required
- **TopSpin integration**: Using jython interface with Java Swing gui
- **Schema-driven**: JSON Schema defines data structure and validation
- **Human-readable storage**: JSON files for metadata persistence
- **Version control friendly**: Text-based storage with clear schema versioning

### System Components

```
┌─ NMR Sample Manager ──────────────────────────┐
│                                               │
│  Web Interface (HTML/JavaScript)             │
│  ├─ Folder selection                         │
│  ├─ Sample list/browser                      │
│  ├─ Form interface (React JSON Schema Form)  │
│  └─ File operations                          │
│                                               │
├─ Data Layer ─────────────────────────────────┤
│  ├─ JSON Schema (validation/structure)       │
│  ├─ JSON files (sample metadata)             │
│  └─ Favourites/templates                     │
│                                               │
├─ TopSpin Integration ───────────────────────┤
│  ├─ aij/aej commands (Python scripts)        │
│  ├─ Directory navigation                     │
│  └─ Sample logging                           │
│                                               │
└───────────────────────────────────────────────┘
```




# Building Persistent GUI Applications in Jython for TopSpin

## Development Environment

### Software Versions
- **Jython**: 2.7.2
- **Java**: 11.0.20 (Eclipse Adoptium)

### Available Libraries
- **JSON handling**: Python's built-in `json` module works fine
- **Swing**: Fully available (part of Java standard library) - use this
- **JavaFX**: Do not use

### Key Limitations
- No C extensions (pure Python libraries only)
- `simplejson` offers no advantage over built-in `json` in Jython
- `localStorage`/`sessionStorage` not available

## The Core Problem

TopSpin's Jython environment executes each script in a separate namespace. This means:
- Traditional Python global variables don't persist between script executions
- Running the same GUI script multiple times creates multiple windows
- No easy way to maintain application state across script runs
- External scripts cannot interact with a running GUI

## The Solution: Java System Properties

Store your application instance in Java's system properties, which persist across script executions within the same JVM session.

```python
from java.lang import System

APP_KEY = "your.unique.app.key"

# Store instance
System.getProperties().put(APP_KEY, your_app_instance)

# Retrieve instance
app = System.getProperties().get(APP_KEY)
```

## Architecture Pattern

### 1. Application Class Structure

```python
from javax.swing import *
from java.awt import *
from java.lang import System

APP_KEY = "topspin.yourapp.instance"

class YourApplication:
    def __init__(self):
        # Define your state variables
        self.state_var1 = None
        self.state_var2 = []
        self.counter = 0
        
        # GUI components
        self.frame = None
        self.status_label = None
        
        self.create_gui()
    
    def create_gui(self):
        """Build the GUI"""
        self.frame = JFrame('Your App Title')
        self.frame.setSize(500, 400)
        
        # CRITICAL: Use HIDE_ON_CLOSE to preserve state
        self.frame.setDefaultCloseOperation(WindowConstants.HIDE_ON_CLOSE)
        
        # Build your GUI components here
        
        self.frame.setVisible(True)
    
    # Public API methods for external control
    def show(self):
        """Show the window if hidden"""
        if self.frame is not None:
            self.frame.setVisible(True)
            self.frame.toFront()
            self.frame.requestFocus()
    
    def hide(self):
        """Hide the window"""
        if self.frame is not None:
            self.frame.setVisible(False)
    
    def your_method(self):
        """Your domain-specific methods"""
        # Modify state
        # Update GUI
        pass
    
    def get_state(self):
        """Return current state as dictionary"""
        return {
            'var1': self.state_var1,
            'var2': self.state_var2,
            'counter': self.counter
        }
```

### 2. Singleton Access Pattern

```python
def get_app():
    """Get or create the application singleton"""
    app = System.getProperties().get(APP_KEY)
    
    if app is None:
        # Create new instance
        app = YourApplication()
        System.getProperties().put(APP_KEY, app)
    else:
        # Version check for code updates
        if not hasattr(app, 'show'):
            # Old version - replace it
            app = YourApplication()
            System.getProperties().put(APP_KEY, app)
        else:
            # Show existing instance
            app.show()
    
    return app

def main():
    get_app()

main()
```

### 3. External Control Script Pattern

```python
from java.lang import System

APP_KEY = "topspin.yourapp.instance"

def get_app():
    """Get the running application instance"""
    return System.getProperties().get(APP_KEY)

def main():
    app = get_app()
    
    if app is None:
        MSG("Application not running - start main GUI first")
        return
    
    # Interact with the application
    app.show()
    app.your_method()
    
    # Query state
    state = app.get_state()
    
    # Optional: hide after interaction
    # app.hide()

main()
```

## Critical Implementation Details

### Window Close Behaviour

```python
# WRONG - destroys window and loses reference
self.frame.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE)

# CORRECT - hides window, preserves state
self.frame.setDefaultCloseOperation(WindowConstants.HIDE_ON_CLOSE)
```

Using `HIDE_ON_CLOSE` means:
- Window disappears when closed
- Application instance remains in memory
- State is preserved
- External scripts can still interact with it
- Calling `show()` brings it back

### Version Management

To avoid problems with updates during development, we need a proper quit/shutdown method that removes the application from system properties, forcing a fresh start next time. Here's how:

```python
def shutdown(self):
    """Properly shut down the application"""
    # Clean up GUI
    if self.frame is not None:
        self.frame.dispose()
    
    # Remove from system properties
    System.getProperties().remove(APP_KEY)
    
    # Optional: display confirmation
    MSG("Application shut down - next run will be fresh instance")
```

You can trigger this in several ways:

**Option 1: Add a Quit button to your GUI**
```python
def create_gui(self):
    # ... other setup ...
    
    btn_quit = JButton('Quit', actionPerformed=lambda event: self.shutdown())
    btn_panel.add(btn_quit)
```

**Option 2: Create a separate shutdown script**
```python
# shutdown_script.py
from java.lang import System

APP_KEY = "topspin.yourapp.instance"

def main():
    app = System.getProperties().get(APP_KEY)
    
    if app is None:
        MSG("No application running")
    else:
        app.shutdown()

main()
```


### Message Dialog Issues

Direct MSG() calls: You can call MSG(...) directly, which avoids parsing issues:

```python
# BEST - call MSG directly
msg = "Status:\nValue: %s" % value
MSG(msg)  # Works fine with newlines and special characters
```

EXEC_PYSCRIPT Issues: When using EXEC_PYSCRIPT('MSG(...)'), the string is parsed as Python code. This causes problems:

```python
# WRONG - newlines and colons cause syntax errors in EXEC_PYSCRIPT
msg = "Status:\nValue: %s" % value
EXEC_PYSCRIPT('MSG("%s")' % msg)  # Fails!

# WORKAROUND - single line format if you must use EXEC_PYSCRIPT
msg = "Status - Value: %s, Count: %d" % (value, count)
EXEC_PYSCRIPT('MSG("%s")' % msg)
```

General EXEC_PYSCRIPT caution: This applies to any code passed to EXEC_PYSCRIPT() - it's parsed and executed as Python, so string formatting issues can cause syntax errors. Use direct function calls when possible.


## State Management Principles

### All State Must Be Instance Variables

```python
def __init__(self):
    self.my_data = []  # ✓ Persists
    local_var = []     # ✗ Disappears after __init__
```

### Provide Clean API Methods

```python
# Public methods for external control
def load_data(self, source):
    """Load data from source"""
    self.data = process(source)
    self.update_display()

def get_current_data(self):
    """Return current data"""
    return self.data

def reset(self):
    """Reset to initial state"""
    self.data = []
    self.counter = 0
    self.update_display()
```

### Update GUI in Response to State Changes

```python
def update_display(self):
    """Refresh GUI to reflect current state"""
    self.status_label.setText("Items: %d" % len(self.data))
    # Update other components
```

## Workflow

### Initial Development
1. Start main script → creates GUI with initial state
2. Interact with GUI → state changes
3. Run main script again → brings existing window to front (no new window)

### External Control
1. Main GUI is running (visible or hidden)
2. Run control script → retrieves singleton instance
3. Control script calls methods → modifies state
4. GUI updates reflect changes
5. Close control script → GUI remains in memory

### State Persistence
- State persists as long as TopSpin (JVM) is running
- Closing the window hides it but preserves state
- Restarting TopSpin clears all state
- For true persistence, implement file-based save/load

## Common Patterns

### Preventing Multiple Windows

```python
# Instead of checking frames by title, use system properties
def get_app():
    app = System.getProperties().get(APP_KEY)
    if app is None or not hasattr(app, 'show'):
        app = YourApplication()
        System.getProperties().put(APP_KEY, app)
    else:
        app.show()
    return app
```

### Adding Status Display

```python
def create_gui(self):
    # Status label that shows current state
    self.status_label = JLabel("Ready")
    status_panel = JPanel(FlowLayout(FlowLayout.LEFT))
    status_panel.add(JLabel("Status: "))
    status_panel.add(self.status_label)
    self.frame.add(status_panel, BorderLayout.NORTH)

def update_status(self, text):
    self.status_label.setText(text)
```

### Building Public API

```python
# Design methods that external scripts will call
class YourApplication:
    # ... __init__ and create_gui ...
    
    # Command methods
    def execute_command(self, cmd, params):
        """Execute a command with parameters"""
        pass
    
    # Query methods
    def get_state(self):
        """Return complete state"""
        return dict(self.__dict__)
    
    def get_item(self, index):
        """Get specific item"""
        return self.items[index] if index < len(self.items) else None
    
    # Control methods
    def show(self):
        """Show window"""
        pass
    
    def hide(self):
        """Hide window"""
        pass
```

## Troubleshooting

### Problem: Multiple Windows Still Appearing
**Cause**: `get_app()` not finding existing instance  
**Solution**: Check `APP_KEY` is exactly the same in all scripts

### Problem: AttributeError After Code Update
**Cause**: Old instance lacks new methods  
**Solution**: Add `hasattr()` check in `get_app()` to force recreation

### Problem: State Resets When Window Closes
**Cause**: Using `DISPOSE_ON_CLOSE` instead of `HIDE_ON_CLOSE`  
**Solution**: Change default close operation to `HIDE_ON_CLOSE`

### Problem: External Script Can't Find App
**Cause**: Main GUI was never started or TopSpin was restarted  
**Solution**: Ensure main script runs first; restart TopSpin clears everything

### Problem: Syntax Error in MSG()
**Cause**: Newlines or special characters in message string  
**Solution**: Use single-line format with commas/hyphens as separators

## Notes

- State only persists within a single TopSpin session
- Restarting TopSpin clears all system properties
- For persistence across sessions, implement file-based save/load using JSON
- All scripts must use the exact same `APP_KEY` value
- The singleton pattern works because all scripts share the same JVM instance