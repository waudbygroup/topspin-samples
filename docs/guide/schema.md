# Understanding the Schema

This guide explains the NMR Sample Metadata schema in plain English. The schema defines what information you can record about your NMR samples and how it's structured.

## What is a Schema?

The schema is like a template or blueprint that defines:

- What fields are available (e.g., "pH", "concentration", "tube type")
- What type of data each field accepts (text, numbers, dropdown choices)
- What values are allowed (e.g., pH must be between 0 and 14)
- How fields are organized into sections

Think of it as a standardized form that ensures everyone in your lab records sample information consistently.

## Schema Version

**Current version: 0.0.3**

The schema evolves over time to add new features and fields. Each sample file records which schema version it was created with, ensuring backwards compatibility.

## Field Reference

### People

Information about who worked with this sample.

#### Users
- **Type**: List of text entries
- **Purpose**: Names of researchers who prepared or worked with the sample
- **Example**: `["Alice Smith", "Bob Jones"]`
- **Why it matters**: Track authorship, know who to ask questions about old samples

#### Groups
- **Type**: List of text entries
- **Purpose**: Research groups involved in the experiment
- **Example**: `["Waudby Lab", "Protein Structure Facility"]`
- **Why it matters**: Important for collaborative projects and facility usage tracking

### Sample

Core information about what's in the NMR tube.

#### Label
- **Type**: Short text
- **Purpose**: Quick identifier for the sample
- **Example**: `"HEWL_pH7_15N"`
- **Why it matters**: Used in filenames, easy reference in notes and discussions

#### Components

Each sample can contain multiple components (proteins, ligands, etc.). For each component:

**Name**
- **Type**: Text
- **Purpose**: Molecule or protein name
- **Example**: `"Hen Egg White Lysozyme"`, `"ATP"`, `"Ubiquitin"`
- **Why it matters**: Know exactly what you're looking at

**Concentration**
- **Type**: Number (≥ 0) or null
- **Purpose**: How much of this component is present
- **Example**: `500`, `1.2`, `0.05`
- **Why it matters**: Critical for quantitative analysis, reproducibility

**Unit**
- **Type**: Dropdown choice
- **Options**: `uM`, `mM`, `M`, `mg/mL`, `%w/v`, `%v/v`, `equiv`
- **Example**: `"uM"` for micromolar
- **Why it matters**: Ensures concentration is unambiguous

**Isotopic Labelling**
- **Type**: Dropdown choice
- **Options**:
  - `unlabelled` - No isotopic labeling
  - `15N` - Nitrogen-15 labeled
  - `13C` - Carbon-13 labeled
  - `13C,15N` - Double labeled
  - `2H,13C,15N` - Triple labeled (deuterated)
  - `Ile-δ1-13CH3` - Specific methyl labeling
  - `Leu/Val-13CH3` - Leucine/Valine methyl labeling
  - `ILV-13CH3` - Ile/Leu/Val methyl labeling
  - `ILV-13CH3,15N` - ILV methyl + 15N backbone
  - `Met-13CH3` - Methionine methyl labeling
  - `Met-13CH3,15N` - Met methyl + 15N backbone
  - `ILVM-13CH3` - Ile/Leu/Val/Met methyl labeling
  - `AILV-13CH3` - Ala/Ile/Leu/Val methyl labeling
  - `custom` - Custom labeling (describe in next field)
- **Why it matters**: Essential for experiment selection, data interpretation, repository submission

**Custom Labelling**
- **Type**: Text (appears if "custom" selected above)
- **Purpose**: Describe non-standard labeling schemes
- **Example**: `"15N-Trp, 13C-His"`
- **Why it matters**: Flexibility for specialized labeling strategies

### Buffer

Buffer composition and solution conditions.

#### pH
- **Type**: Number (0-14) or null
- **Purpose**: Solution pH
- **Example**: `7.4`, `6.5`, `8.0`
- **Why it matters**: Critical experimental parameter, affects protein behavior

#### Components

Buffer components like salts, buffering agents, additives. Each has:

**Name**
- **Type**: Text
- **Example**: `"Tris-HCl"`, `"NaCl"`, `"EDTA"`, `"DTT"`
- **Why it matters**: Complete buffer composition for reproducibility

**Concentration**
- **Type**: Number (≥ 0) or null
- **Example**: `50`, `150`, `1`
- **Why it matters**: Exact buffer recipe

**Unit**
- **Type**: Dropdown choice
- **Options**: `uM`, `mM`, `M`, `mg/mL`, `%w/v`, `%v/v`, `%w/w`
- **Why it matters**: Unambiguous concentration specification

#### Chemical Shift Reference
- **Type**: Dropdown choice
- **Options**:
  - `none` - No reference compound added
  - `DSS` - 4,4-dimethyl-4-silapentane-1-sulfonic acid (most common)
  - `TMS` - Tetramethylsilane
  - `TSP` - Trimethylsilylpropanoic acid
- **Purpose**: Standard for calibrating chemical shift scales
- **Why it matters**: Essential for accurate chemical shift reporting, data deposition

#### Reference Concentration
- **Type**: Number (≥ 0) or null
- **Purpose**: Concentration of the chemical shift reference
- **Example**: `0.5`, `1.0`
- **Why it matters**: Some analysis methods need to know reference concentration

#### Reference Unit
- **Type**: Dropdown choice
- **Options**: `uM`, `mM`, `M`, `mg/mL`, `%w/v`, `%v/v`, `%w/w`
- **Purpose**: Unit for reference concentration
- **Why it matters**: Complete reference specification

#### Solvent
- **Type**: Dropdown choice
- **Options**:
  - `10% D2O` - Common for protein NMR (H2O with lock)
  - `100% D2O` - Fully deuterated (no water signal)
  - `CDCl3` - Deuterated chloroform (organic chemistry)
  - `D6-DMSO` - Deuterated DMSO
  - `D4-Methanol` - Deuterated methanol
  - `custom` - Other solvents
- **Purpose**: Solvent composition, especially D2O content
- **Why it matters**: Affects experiment selection, influences spectra

#### Custom Solvent
- **Type**: Text (appears if "custom" selected above)
- **Purpose**: Describe non-standard solvent mixtures
- **Example**: `"50% D2O / 50% CD3OD"`
- **Why it matters**: Flexibility for special applications

### NMR Tube

Physical properties of the NMR tube itself.

#### Diameter
- **Type**: Dropdown choice
- **Options**: `1.7 mm`, `3 mm`, `5 mm`
- **Purpose**: Tube diameter
- **Why it matters**: Different tubes need different probes, affects sensitivity

#### Type
- **Type**: Dropdown choice
- **Options**:
  - `regular` - Standard glass NMR tube
  - `shigemi` - Shigemi tube (susceptibility-matched glass plugs)
  - `shaped` - Shaped tube (e.g., for limited sample volumes)
  - `coaxial` - Coaxial tube (for reference samples)
- **Purpose**: Specialized tube types
- **Why it matters**: Affects data quality, sample volume requirements

#### Sample Volume (μL)
- **Type**: Number or null
- **Purpose**: Sample volume in microliters
- **Example**: `350`, `600`, `180`
- **Why it matters**: Track precious samples, plan experiments

#### SampleJet Rack Position
- **Type**: Text
- **Purpose**: Position in SampleJet automation system
- **Example**: `"A3"`, `"G11"`, `"B7"`
- **Why it matters**: Essential for automated sample changers, tracking physical location

#### SampleJet Rack ID
- **Type**: Text
- **Purpose**: Identifier for which rack is being used
- **Example**: `"Rack-001"`, `"UserA-Rack1"`
- **Why it matters**: Track multiple racks, avoid mix-ups in busy facilities

### Laboratory Reference

Links to external documentation and lab systems.

#### Sample ID
- **Type**: Text
- **Purpose**: Local identifier in your lab's sample tracking system
- **Example**: `"CW-2025-042"`, `"Sample-789"`
- **Why it matters**: Connect NMR data to broader lab records

#### Labbook Entry
- **Type**: Text
- **Purpose**: Reference to lab notebook page or electronic entry
- **Example**: `"LB-2025-10-23-p15"`, `"ELN-Entry-1234"`
- **Why it matters**: Link spectral data to sample preparation notes

### Notes

- **Type**: Free-form text (can be long)
- **Purpose**: Any additional information that doesn't fit in structured fields
- **Example**:
  ```
  Sample prepared 24h before NMR.
  Slight precipitation observed after 3 days at 298K.
  Re-centrifuged before experiment 15.
  ```
- **Why it matters**: Capture important observations that structured fields can't express

### Metadata

Automatic fields managed by Sample Manager. These are not directly editable.

#### Schema Version
- **Type**: Text
- **Purpose**: Version of schema used for this sample
- **Example**: `"0.0.3"`
- **Why it matters**: Ensures backwards compatibility as schema evolves

#### Created Timestamp
- **Type**: Date/time (ISO 8601 format)
- **Purpose**: When this sample record was created
- **Example**: `"2025-10-23T14:30:22.000Z"`
- **Why it matters**: Marks sample injection time, creates filename

#### Modified Timestamp
- **Type**: Date/time (ISO 8601 format)
- **Purpose**: When this record was last edited
- **Example**: `"2025-10-23T16:15:30.000Z"`
- **Why it matters**: Track when changes were made

#### Ejected Timestamp
- **Type**: Date/time (ISO 8601 format) or null
- **Purpose**: When sample was removed from spectrometer
- **Example**: `"2025-10-24T10:45:00.000Z"` or `null` (still active)
- **Why it matters**: Mark end of sample lifetime, enable "active sample" logic

## Required vs. Optional Fields

**All fields are optional!**

The schema doesn't force you to fill in every field. Enter what's relevant for your sample - you can always add more information later.

However, we recommend at minimum:
- Sample label
- At least one user
- Basic sample composition (name, concentration)
- pH (for protein NMR)

## Example: Complete Sample

Here's what a fully-filled sample looks like:

```json
{
  "people": {
    "users": ["Chris Waudby"],
    "groups": ["Waudby Lab"]
  },
  "sample": {
    "label": "HEWL_pH7_15N",
    "components": [{
      "name": "Hen Egg White Lysozyme",
      "concentration": 500,
      "unit": "uM",
      "isotopic_labelling": "15N"
    }]
  },
  "buffer": {
    "ph": 7.4,
    "components": [
      {
        "name": "Tris-HCl",
        "concentration": 50,
        "unit": "mM"
      },
      {
        "name": "NaCl",
        "concentration": 100,
        "unit": "mM"
      }
    ],
    "chemical_shift_reference": "DSS",
    "reference_concentration": 0.5,
    "reference_unit": "mM",
    "solvent": "10% D2O"
  },
  "nmr_tube": {
    "diameter": "5 mm",
    "type": "shigemi",
    "sample_volume_uL": 350,
    "samplejet_rack_position": "A3",
    "samplejet_rack_id": "Rack-001"
  },
  "reference": {
    "sample_id": "CW-2025-042",
    "labbook_entry": "ELN-2025-10-23"
  },
  "notes": "Sample prepared fresh on day of experiment. Stable for 3 days at 298K.",
  "metadata": {
    "schema_version": "0.0.3",
    "created_timestamp": "2025-10-23T14:30:22.000Z",
    "modified_timestamp": "2025-10-23T14:35:10.000Z",
    "ejected_timestamp": "2025-10-24T10:45:00.000Z"
  }
}
```

## Schema Evolution

The schema is maintained in a [separate repository](https://github.com/waudbygroup/nmr-sample-schema) and evolves based on community feedback.

### Version History

**v0.0.3** (Current)
- Reorganized structure with `people`, `sample`, `buffer`, etc. top-level objects
- Added `groups` field for research groups
- Expanded isotopic labeling options for methyl-labeled proteins
- Added custom labeling and custom solvent fields
- Improved field descriptions

**v0.0.2**
- Added chemical shift reference concentration and unit
- Expanded tube type options

**v0.0.1**
- Initial schema release

### Proposing Changes

Want to suggest a new field or change?

1. Open an issue in the [schema repository](https://github.com/waudbygroup/nmr-sample-schema/issues)
2. Describe what field you need and why
3. Community discussion and consensus
4. Schema maintainers implement in next version

## Related Tools

All these tools use the same schema:

- **[topspin-samples](https://github.com/waudbygroup/topspin-samples)** (this application) - TopSpin integration
- **[nmr-sample-viewer](https://github.com/waudbygroup/nmr-sample-viewer)** - Web-based viewer/editor
- **[nmr-sample-schema](https://github.com/waudbygroup/nmr-sample-schema)** - Schema repository

Any changes to the schema are automatically picked up by all tools.

---

Questions about the schema? [Contact us](mailto:c.waudby@ucl.ac.uk) or [open an issue](https://github.com/waudbygroup/nmr-sample-schema/issues).
