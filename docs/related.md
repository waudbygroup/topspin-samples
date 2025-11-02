# Ecosystem

Sample Manager is part of an ecosystem built around a shared JSON schema. Your sample metadata files are portable - they can be read and edited by multiple tools.

## nmr-sample-schema

**Repository:** [github.com/waudbygroup/nmr-sample-schema](https://github.com/waudbygroup/nmr-sample-schema)

The JSON schema that defines NMR sample metadata structure is maintained independently with semantic versioning and community-driven development. Maintaining the schema separately allows multiple tools to use the same standard and enables version control independent of application code.

All tools in the ecosystem use this shared schema, ensuring compatibility and data portability.

## nmr-sample-viewer

**Repository:** [github.com/waudbygroup/nmr-sample-viewer](https://github.com/waudbygroup/nmr-sample-viewer)

A web-based application for viewing and editing NMR sample metadata offline without TopSpin.

![Web Viewer](images/web-viewer.png)

Features:

- Browser-based access with no installation required
- Works offline using the File System Access API
- Search and filtering across directories
- Bulk operations for creating and editing multiple samples

**When to use each tool:**

- Use Sample Manager during data acquisition for TopSpin integration
- Use the web viewer for data review, searching across projects, and sharing with collaborators who don't have TopSpin

## Why Separate Tools?

The TopSpin integration and web viewer serve different needs:

- **Sample Manager** runs in TopSpin's Jython environment, integrates with your workflow, and captures metadata during data acquisition
- **Web Viewer** runs in any modern browser, works on any operating system, and provides powerful search across your entire sample history

Both tools read and write identical JSON files, so you can use whichever tool suits your current task.
