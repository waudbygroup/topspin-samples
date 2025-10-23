# Tips & Tricks

Power user features and best practices for getting the most out of Sample Manager.

## Workflow Integration

### Integrate with Your Daily Routine

Build Sample Manager into your standard NMR workflow:

1. **Load sample physically** → Type `ija` → Fill form → Save
2. **Run experiments** as normal in TopSpin
3. **Check timeline** periodically to review progress
4. **Eject sample** → Type `eja`

After a few samples, this becomes second nature.

### Command Aliases

If you prefer shorter commands, you could create TopSpin command aliases:

- `ija` → Consider it as "inject and annotate"
- `eja` → Consider it as "eject and annotate"
- `samples` → Main GUI

The short commands make integration seamless.

## Template Management

### Create Template Library

Build a collection of templates for common sample types:

```
~/nmr-templates/
├── protein_15N.json
├── protein_13C15N.json
├── protein_ILV_methyl.json
├── ligand_binding.json
└── small_molecule.json
```

**To use a template:**

1. Copy template JSON to your data directory
2. Open Sample Manager
3. Select the template
4. Click "Duplicate..."
5. Modify for your specific sample
6. Save

### Facility-Wide Templates

For core facilities, create standardized templates:

- Store in shared network location
- Document in facility user manual
- Train new users on template usage
- Update templates when schema changes

This ensures consistent metadata across all users.

## Naming Conventions

### Develop a Labeling Scheme

Consistent sample labels make searching and organizing easier:

**Example schemes:**

```
# By protein and condition
HEWL_pH7_298K
HEWL_urea_298K
Ubiquitin_pH6.5_310K

# By project and sample number
Project_Sample_Condition
TitrationA_001_pH7.0
TitrationA_002_pH7.5

# By date and identifier
YYYYMMDD_Protein_Condition
20251023_HEWL_native
20251024_HEWL_denatured
```

Pick a scheme that works for your lab and stick to it.

### Use Descriptive Labels

Labels appear in:
- Filenames
- Sample list
- Timeline view
- Search results

Make them informative but concise:

- ✅ Good: `HEWL_pH7_15N_shigemi`
- ❌ Too vague: `sample1`
- ❌ Too long: `Hen_Egg_White_Lysozyme_in_50mM_Tris_pH_7_point_4_with_100mM_NaCl_15N_labeled`

## Data Organization

### Directory Structure

Organize your NMR data directories logically:

```
/data/username/nmr/
├── 2025-10-HEWL-titration/
│   ├── 2025-10-23_140000_HEWL_pH7.json
│   ├── 2025-10-23_160000_HEWL_pH6.json
│   └── 1/ 2/ 3/ ... (experiments)
├── 2025-10-ubiquitin/
│   ├── 2025-10-24_100000_Ub_native.json
│   └── 1/ 2/ 3/ ... (experiments)
└── templates/
    └── (template JSON files)
```

This keeps related experiments together and makes backups easier.

### Sample Versioning

If you modify a sample (e.g., add ligand), you have two options:

**Option 1: Edit existing sample**
- Good for: Minor adjustments (pH, temperature)
- Preserves sample history
- Modified timestamp tracks changes

**Option 2: Create new sample and eject old**
- Good for: Major changes (added component, different concentration)
- Clear separation in timeline
- Each sample has distinct metadata

Choose based on whether you want one continuous record or separate samples.

## Advanced Timeline Usage

### Reading the Timeline

The timeline tells a story of your experiment:

```
14:30 - Sample Created: HEWL_pH7 (A3)
14:45 - Exp 1: PROTON (quick check)
15:00 - Exp 2: HSQC (initial spectrum)
15:30 - Exp 3: HSQC (repeat after shimming)
16:00 - Exp 4-18: HSQC series (titration)
18:30 - Sample Ejected
```

Use this to:
- Document experimental timeline
- Check acquisition order
- Identify gaps or issues
- Generate methods sections for papers

### Timeline for Troubleshooting

Timeline helps diagnose problems:

**Example: "Why did my HSQC look weird?"**

Check timeline:
- Was a different sample loaded? (check sample created timestamp)
- Was there a long gap suggesting sample degradation?
- Did previous experiments run successfully? (check experiment list)

### Timeline for Publications

Generate accurate experimental descriptions:

> "15N-labeled HEWL (500 μM) in 50 mM Tris-HCl, pH 7.4, 10% D2O with 0.5 mM DSS as chemical shift reference. Data collected at 298 K as a series of 15 2D 1H-15N HSQC spectra (experiments 4-18) over 4 hours."

All this information is in your sample JSON and timeline.

## Batch Operations

### Multiple Samples Per Directory

Sample Manager supports multiple samples in one directory (common for SampleJet):

```
/data/screening-project/
├── 2025-10-23_140000_compound_A.json  (A1)
├── 2025-10-23_143000_compound_B.json  (A2)
├── 2025-10-23_150000_compound_C.json  (A3)
└── 1/ 2/ 3/ ... (experiments)
```

Use the timeline to see which experiments correspond to which samples.

### SampleJet Workflows

For automated sample changers:

1. **Pre-create samples**: Use "Duplicate..." to create all samples before starting
2. **Set rack positions**: Fill in SampleJet rack position for each
3. **Save all samples**: Each gets unique timestamp
4. **Run SampleJet**: Let automation do its work
5. **Review timeline**: Check all samples were run correctly

The timeline will show sample injections/ejections interleaved with experiments.

## Data Backup and Sharing

### Include JSON in Backups

When backing up NMR data:

```bash
# Backup entire directory including JSON
rsync -av /opt/topspin/data/user/nmr/project/ /backup/location/

# Or specifically include JSON
rsync -av --include="*.json" /opt/topspin/data/user/ /backup/
```

JSON files are small (typically <5 KB) and compress well.

### Share Metadata with Collaborators

Send sample JSON with your NMR data:

```bash
# Create archive with data and metadata
tar czf HEWL_project.tar.gz \
  /path/to/data/ \
  --include="*.json"
```

Collaborators can view JSON files:
- In any text editor
- With the [web-based viewer](https://github.com/waudbygroup/nmr-sample-viewer)
- With Sample Manager if they have TopSpin

### Version Control for Metadata

For research projects, track JSON files with git:

```bash
cd /path/to/project
git init
git add *.json
git commit -m "Initial sample metadata"
```

This creates a full history of sample metadata changes.

## Schema Customization (Advanced)

### Local Schema Modifications

If you need custom fields for your lab, you can modify the schema locally:

1. Edit `src/schemas/current/schema.json`
2. Add your custom fields following JSON Schema syntax
3. Restart Sample Manager

**Example: Add "Storage Location" field**

```json
"reference": {
  "properties": {
    "storage_location": {
      "title": "Storage Location",
      "type": "string",
      "description": "Physical location where sample is stored"
    }
  }
}
```

!!! warning "Schema Compatibility"
    Local schema changes won't be recognized by other tools (web viewer, other installations). For shared changes, propose them to the [schema repository](https://github.com/waudbygroup/nmr-sample-schema).

## Troubleshooting Tips

### Sample Manager Not Responding

If Sample Manager GUI freezes or becomes unresponsive:

1. **Close the window** (click X or minimize)
2. **Restart TopSpin** (this clears the application state)
3. **Type `samples` again** to start fresh

The singleton pattern means state persists until TopSpin restarts.

### JSON File Errors

If you manually edit JSON and break it:

1. **Check syntax** - Use a JSON validator (jsonlint.com)
2. **Compare with working sample** - Copy structure from a valid file
3. **Start over** - Create new sample, copy values from broken file

Common JSON errors:
- Missing comma between fields
- Trailing comma after last field
- Unmatched brackets/braces
- Unquoted strings or improperly escaped quotes

### Timeline Missing Experiments

If experiments don't appear in timeline:

- **Check `acqus` file exists** - Timeline parses this file
- **Check directory is integer** - Only numbered directories (1, 2, 3...) are included
- **Check for errors in acqus** - Corrupted files may not parse

### Missing Schema Versions

If you get a schema version error:

```
Error: Schema version 0.0.2 not found
Expected at: src/schemas/versions/v0.0.2/schema.json
```

**Solution**: Update Sample Manager

```bash
cd /path/to/topspin-samples
git pull
```

This downloads missing schema versions.

## Performance Tips

### Large Directories

For directories with hundreds of experiments:

- Timeline may take a few seconds to load (parsing all acqus files)
- Consider organizing projects into smaller directories
- Sample list is always fast (only loads JSON files)

### Network File Systems

If your NMR data is on a network drive:

- File operations may be slower
- Consider local templates, then save to network
- Close Sample Manager when not in use to reduce network traffic

## Next Steps

Now you're a Sample Manager power user! Help improve the tool:

- **[Suggest features](https://github.com/waudbygroup/topspin-samples/issues)** - What would make your workflow better?
- **[Contribute code](../contributing.md)** - Fix bugs or add features
- **[Propose schema changes](https://github.com/waudbygroup/nmr-sample-schema/issues)** - New fields you need
- **[Share your experience](mailto:c.waudby@ucl.ac.uk)** - Help us improve documentation

---

Have a tip to share? [Open an issue](https://github.com/waudbygroup/topspin-samples/issues) or [contact us](mailto:c.waudby@ucl.ac.uk)!
