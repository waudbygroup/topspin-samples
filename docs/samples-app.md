# The Samples App

The samples app is a GUI for viewing and searching your sample history. Launch it by typing `samples` in TopSpin. The window opens automatically in your current dataset's directory, and you'll immediately see the timeline of everything you've been running.

## Opening the App

Type `samples` in TopSpin's command line. The GUI window appears and navigates to your current dataset directory. If the window is already open, typing `samples` brings it to the front.

![Sample Manager main window](images/sample-catalogue.png)

The interface has three main areas:

- **Directory navigation** at the top - browse to any NMR data directory or jump to TopSpin's current dataset
- **Three tabs** in the middle - Samples, Timeline, and Catalogue views
- **Action buttons** at the bottom - New, Edit, Duplicate, Mark as Ejected, Delete
- **Status bar** - shows current directory, active sample status, and sample count

## Timeline View

The timeline shows all your experiments in chronological order, colour-coded by dimensionality (black = 1D, blue = 2D, green = 3D+).

![Timeline View](images/timeline.png)

Even if you've never created sample annotations, the timeline gives you a view of what you've been running. You can see experiment types and when each dataset was created. If you have defined samples, then experiments are clearly associated with this in the timeline.

**Special feature for SampleJet users**: Holder positions from your experiments automatically appear in the Holder column, even without any sample annotations. The system reads the SampleJet position from experiment parameters and displays it in the timeline.

**Double-click to open**: Click any experiment row to open that dataset in TopSpin. This makes the timeline a navigable index of your data.

### Creating Samples Retrospectively

Forgot to annotate when you injected a sample? No problem.

![Retrospective Sample Creation](images/retrospective-sample-creation.png)

Right-click in the timeline and select the experiments that correspond to a single sample. The system figures out the timing automatically:

- Created timestamp = time of first selected experiment
- Ejected timestamp = time of last selected experiment

Fill in the form with your sample details and save. The annotation appears in the timeline as if you'd created it at the time.

## Catalogue View

The catalogue shows all samples across your configured root directories, with search capabilities.

![Sample Catalogue](images/sample-catalogue.png)

**Use cases**:

- "Find that sample where I used HEPES buffer last summer"
- "Show me all samples that Chris worked on in 2024"
- "Which samples used 15N-labelled ubiquitin?"

**Filtering**: Filter by users, sample components, buffer compositions, or any text in the sample label or notes.

**Setup**: Configure root directories via Settings to enable multi-directory browsing. The catalogue scans all configured directories and builds a searchable index.

## Samples Tab

The samples tab lists all sample JSON files in the current directory.

Each row shows:

- Filename (with timestamp and sample label)
- Status (ACTIVE or ejection time)
- Sample label
- Users who worked with the sample

Click a sample to select it (enables the action buttons). Double-click to open the editing form.

## Creating New Samples

Click "New..." to create a sample annotation. A form opens with several sections.

![Sample Form](images/editing-sample-buffer.png)

All fields are optional - fill in what matters for your work:

- **People**: Users, research groups
- **Sample**: Label, components (name, concentration, isotopic labelling)
- **Buffer**: pH, solvent, chemical shift reference, buffer components
- **NMR Tube**: Diameter, type (regular, Shigemi, etc), sample volume, SampleJet rack position
- **Laboratory Reference**: Sample ID, lab book entry
- **Notes**: Free-form text

When you save, the system creates a JSON file with format `YYYY-MM-DD_HHMMSS_[label].json`. The timestamp marks when the sample was created (injection time).

**One active sample rule**: Creating a new sample automatically ejects any previously active sample in the directory. This matches physical reality - you can only have one sample in the magnet at a time.

## Editing Samples

Select a sample and click "Edit" (or double-click) to modify it. Samples display in read-only mode initially; editing enables the form fields.

Make your changes and click "Save". The `modified_timestamp` updates automatically.

## Duplicating Samples

Select a sample and click "Duplicate..." to copy it as a template. The form opens with all fields pre-filled. Modify what's different (e.g., concentration, pH, tube type) and save as a new sample.

This is particularly useful when running a series of related samples where only a few parameters change.

## Ejecting Samples

Select the active sample and click "Mark as Ejected". This adds an ejection timestamp to the metadata, marking when the sample was removed from the spectrometer.

The button is only enabled for active (non-ejected) samples. Once ejected, a sample's status changes from "ACTIVE" to showing the ejection date and time.

## Deleting Samples

Select an ejected sample and click "Delete" to permanently remove the JSON file. Active samples cannot be deleted - they must be ejected first.

This is a destructive operation with no undo. The sample metadata is lost, but experiment data remains unaffected (Sample Manager only reads and writes JSON files).

## Directory Navigation

Use "Browse..." to select any NMR data directory. The app scans the directory for sample JSON files and experiment folders, then updates all three tabs.

Use "Go to current dataset" to navigate to TopSpin's currently active dataset directory. This is useful after switching datasets in TopSpin.

## File Storage

Sample metadata files live in your NMR data directories alongside experiments:

```
/data/user/project/
├── 2025-10-23_143022_lysozyme.json
├── 2025-10-23_163045_ubiquitin.json
├── 1/
├── 2/
├── 3/
...
```

The JSON files are human-readable text. You can edit them manually if needed, but the GUI is recommended to avoid syntax errors.

## Schema Versioning

New samples use the current schema version (shown in the status bar). When opening old samples created with previous schema versions, Sample Manager automatically loads the correct historical schema.

When you save an old sample, it's upgraded to the current schema version. This ensures backwards compatibility while allowing the data model to evolve.

If a sample requires a schema version that's not installed, an error panel displays with instructions to update your installation via `git pull`.

---

**Next**: Learn about [Physical Sample Handling](physical-sample-handling.md) - workflow commands that capture metadata during injection/ejection.

**Questions?** [Contact us](mailto:c.waudby@ucl.ac.uk) or [open an issue](https://github.com/nmr-samples/topspin/issues).
