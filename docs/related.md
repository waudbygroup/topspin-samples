# Related Projects

Sample Manager is part of an ecosystem of tools for NMR sample metadata management. All tools share the same JSON schema, making your metadata portable across different applications and workflows.

## Core Projects

### nmr-sample-schema

**Repository:** [github.com/waudbygroup/nmr-sample-schema](https://github.com/waudbygroup/nmr-sample-schema)

The shared JSON schema that defines the structure of NMR sample metadata.

**Key features:**

- Semantic versioning for schema evolution
- JSON Schema format (widely supported)
- Community-driven development
- Documentation for all fields
- Migration guides between versions

**Why it's separate:**

Maintaining the schema independently allows:
- Multiple tools to use the same standard
- Community input from diverse users
- Version control independent of application code
- Easy adoption by other projects

**Current version:** 0.0.3

**How to contribute:**

- Propose new fields via [GitHub Issues](https://github.com/waudbygroup/nmr-sample-schema/issues)
- Discuss with NMR community
- Schema maintainers version and release
- All tools automatically pick up changes

---

### nmr-sample-viewer

**Repository:** [github.com/waudbygroup/nmr-sample-viewer](https://github.com/waudbygroup/nmr-sample-viewer)

A web-based application for viewing and editing NMR sample metadata offline, without TopSpin.

**Key features:**

- **Browser-based** - No installation required
- **Offline capable** - Works without internet connection
- **File System Access API** - Read/write local JSON files directly
- **Same schema** - Full compatibility with Sample Manager
- **Search and filter** - Find samples across directories
- **Catalogue view** - Browse all samples in a project

**Use cases:**

1. **View samples without TopSpin**
   - Data analysis on laptops
   - Sharing data with collaborators
   - Preparing manuscripts

2. **Bulk metadata creation**
   - Create multiple samples at once
   - Import from CSV/Excel
   - Batch editing

3. **Cross-platform access**
   - Works on Windows, Mac, Linux
   - Mobile device viewing (read-only)
   - Any modern web browser

4. **Archive searching**
   - Search through historical data
   - Filter by date, user, composition
   - Export search results

**Architecture:**

- **HTML/JavaScript** - Static web application
- **React JSON Schema Form** - Automatic form generation
- **File System Access API** - Direct file operations
- **No backend** - Everything runs in browser

**Relationship to Sample Manager:**

- **Same JSON files** - Both tools read/write identical format
- **Same schema** - Synchronized schema versions
- **Complementary use** - TopSpin integration vs. standalone viewing
- **Independent operation** - No communication between tools

**Screenshots:**

![Web-based sample viewer](images/web-viewer.png)

*Web viewer showing sample catalogue and form interface*

---

## Comparison: Sample Manager vs. Web Viewer

| Feature | Sample Manager (TopSpin) | Web Viewer |
|---------|--------------------------|------------|
| **Platform** | TopSpin only | Any browser |
| **Installation** | Git clone + Python path | Open URL |
| **TopSpin Integration** | Native commands (`ija`, `eja`) | None |
| **Timeline View** | ✅ Integrated with experiments | ❌ Samples only |
| **Bulk Operations** | ❌ One at a time | ✅ Batch create/edit |
| **Search** | ❌ Current directory only | ✅ Cross-directory search |
| **Catalogue View** | ❌ | ✅ Visual browsing |
| **Auto-navigation** | ✅ Current dataset | ❌ Manual selection |
| **Best for** | Daily NMR workflow | Data review & analysis |

### When to Use Each Tool

**Use Sample Manager (TopSpin) when:**

- You're actively acquiring NMR data
- You want automatic directory navigation
- You need timeline integration
- You want `ija`/`eja` workflow commands

**Use Web Viewer when:**

- Reviewing data without TopSpin
- Searching across multiple projects
- Batch creating samples for planned experiments
- Sharing data with non-TopSpin users
- Working on a laptop or tablet

**Use Both:**

Many users benefit from both tools:

1. **During acquisition** - Use Sample Manager for real-time annotation
2. **During analysis** - Use Web Viewer to search and review all samples
3. **For publication** - Use Web Viewer to find and verify sample details
4. **For collaboration** - Share JSON files, collaborators use Web Viewer

## Future Tools

The shared schema enables development of additional tools:

### Potential Applications

**Data Repository Submission Tool**

- Read sample metadata
- Generate BMRB/PDB submission files
- Validate completeness
- Auto-fill required fields

**Laboratory Information Management System (LIMS) Integration**

- Sync with lab LIMS
- Import sample preparation details
- Export NMR results
- Track sample lifecycle

**Analysis Pipeline Integration**

- Read metadata in Python/R scripts
- Filter samples by criteria
- Generate analysis reports
- Correlate results with sample composition

**Facility Management Dashboard**

- Track spectrometer usage by sample
- Monitor SampleJet operations
- Generate usage statistics
- Invoice by sample

### Want to Build Something?

The schema is open and documented! If you build a tool that uses the nmr-sample-schema:

1. **Let us know** - We'll add it to this page
2. **Share with community** - Help other NMR users
3. **Contribute schema improvements** - Your use case may need new fields
4. **Join the ecosystem** - Build on a shared standard

Contact: [c.waudby@ucl.ac.uk](mailto:c.waudby@ucl.ac.uk)

## Related Standards

The nmr-sample-schema is inspired by and compatible with existing NMR and structural biology standards:

### BMRB (Biological Magnetic Resonance Bank)

- Repository for NMR data
- Sample metadata is required for deposition
- Our schema fields map to BMRB requirements
- Potential future: direct export to BMRB format

**Website:** [bmrb.io](https://bmrb.io)

### PDB (Protein Data Bank)

- Repository for protein structures
- NMR structures require experimental metadata
- Sample conditions affect structure quality
- Our schema captures relevant parameters

**Website:** [rcsb.org](https://www.rcsb.org)

### ISA Framework

- Investigation-Study-Assay framework
- General experimental metadata standard
- Our schema is ISA-compatible in principle
- Potential integration for multi-omics projects

**Website:** [isa-tools.org](https://isa-tools.org)

## Community Resources

### Repositories

- **Sample Manager:** [github.com/waudbygroup/topspin-samples](https://github.com/waudbygroup/topspin-samples)
- **Schema:** [github.com/waudbygroup/nmr-sample-schema](https://github.com/waudbygroup/nmr-sample-schema)
- **Web Viewer:** [github.com/waudbygroup/nmr-sample-viewer](https://github.com/waudbygroup/nmr-sample-viewer)

### Get Involved

- **Report issues** - All repositories have GitHub Issues
- **Suggest features** - Community input drives development
- **Contribute code** - Pull requests welcome
- **Share your use case** - Help us understand diverse needs
- **Build complementary tools** - Extend the ecosystem

### Contact

- **Chris Waudby** - [c.waudby@ucl.ac.uk](mailto:c.waudby@ucl.ac.uk)
- **GitHub Discussions** - Coming soon
- **NMR community forums** - Share your experiences

---

Together, we're building better tools for the NMR community!
