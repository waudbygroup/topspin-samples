# Related Projects

Sample Manager is part of an ecosystem built around a shared JSON schema, making your metadata portable across different applications.

## nmr-sample-schema

**Repository:** [github.com/waudbygroup/nmr-sample-schema](https://github.com/waudbygroup/nmr-sample-schema)

The JSON schema that defines NMR sample metadata structure is maintained independently with semantic versioning and community-driven development. Maintaining the schema separately allows multiple tools to use the same standard and enables version control independent of application code.

## nmr-sample-viewer

**Repository:** [github.com/waudbygroup/nmr-sample-viewer](https://github.com/waudbygroup/nmr-sample-viewer)

A web-based application for viewing and editing NMR sample metadata offline without TopSpin. It provides browser-based access with no installation required, works offline using the File System Access API, includes search and filtering across directories, and offers bulk operations for creating and editing multiple samples. Use Sample Manager during data acquisition with TopSpin integration, and use the web viewer for data review, searching across projects, and sharing with collaborators who don't have TopSpin.

![Web Viewer](images/web-viewer.png)
