# NMR Sample Manager

A standalone web application for managing NMR sample metadata in TopSpin environments.

NMR workflows focus on data acquisition and processing, but sample tracking has been a longstanding blind spot. Bruker software manages *experiments* effectively, but provides no systematic way to record or retrieve information about *samples* -- e.g. protein concentrations, buffer compositions, isotopic labelling schemes, chemical shift referencing, NMR tube types. This often causes problems when looking back over old data or preparing data for repository submission.

Here we describe a simple JSON schema for recording sample metadata, creating a lightweight, parallel system that captures sample information alongside TopSpin workflows.

## Quick Start

1. **Open Application**: Navigate to `src/index.html` in Chrome or Edge
2. **Set Root Directory**: Click "Set" next to "Root:" and select your NMR data folder
3. **Browse Experiments**: Click "Browse" to navigate to specific experiment folders
4. **Manage Samples**: Use "New Sample", "Duplicate", "Edit", or "Eject" buttons
5. **View Timeline**: Click "Show timeline" to see complete history of experiments and samples

## Features

- **Privacy**: No data leaves your computer
- **Zero Installation**: Works immediately on any Chrome/Edge laboratory computer
- **Timeline Visualization**: Track sample/experiment history
- **JSON Schema**: Structured, validated metadata collection

## Browser Requirements

- Chrome, Chromium, Edge (File System Access API support)

Other browsers not currently tested/supported.

## Data Model

Sample metadata is stored as human-readable JSON files with schema validation:

```json
{
  "Users": ["researcher1", "researcher2"],
  "Sample": {
    "Label": "MyProtein_pH7",
    "Components": [{
      "Name": "MyProtein",
      "Isotopic labelling": "15N",
      "Concentration": 500, "unit": "uM"
    }]
  },
  "Buffer": {
    "Components": [{"name": "Tris-HCl", "concentration": 50, "unit": "mM"}],
    "pH": 7.4,
    "Solvent": "10% D2O"
  },
  "NMR Tube": {"Diameter": "5mm", "Type": "shigemi"},
  "Sample Position": {"Rack Position": "A3", "Rack ID": "Rack-001"},
  "Laboratory Reference": {"Labbook Entry": "LB2025-08-001"},
  "Notes": "Sample prepared for HSQC experiments"
}
```