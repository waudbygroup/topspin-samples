# NMR Sample Manager for TopSpin

## The Problem

NMR spectroscopy has excellent software for managing experiments, but sample tracking has always been a blind spot. When you return to old datasets months or years later, can you confidently answer what the protein concentration was, what buffer was used, or what isotopic labelling scheme was employed? Most NMR users rely on lab notebooks, inconsistent text files, or memory, which becomes a real problem when preparing data for repository submission, writing publications, or troubleshooting experiments.

## What It Does

Sample Manager provides:

- A GUI application for viewing and searching sample history (launch with `samples` command)
- Commands to inject and eject samples with parallel metadata annotation (`ija`, `eja`, and `sxa` commands)

## Why This Matters

**Right now**: See what you've been running, organised by sample. Even without annotations, the timeline gives you a birds-eye view of your data.

**This year**: Never again wonder what buffer you used last month. Search across all your samples to find "that 50 mM phosphate sample from August".

**Long term**: Complete documentation for papers, thesis chapters, and data repository submissions. Future you will thank present you.

**For the group**: Track who's running what, maintain sample history when people leave. Lab memory that doesn't walk out the door.

## Get Started

**Installation takes 5 minutes**: Clone the repository, add it to TopSpin's Python path, type `samples`.

[Install Now →](installation.md){ .md-button .md-button--primary }

Once installed, you'll immediately see your timeline. Start annotating samples when you remember - there's no penalty for forgetting because you can create annotations retrospectively by selecting experiments from the timeline.

## Learn More

- [**The Samples App**](samples-app.md) - What you can do with the GUI (timeline, catalogue, search)
- [**Physical Sample Handling**](physical-sample-handling.md) - Workflow commands (`ija`, `eja`, `sxa`) that capture metadata during injection/ejection
- [**Ecosystem**](related.md) - Web viewer for offline access, shared JSON schema for portability

---

**Author**: Chris Waudby, UCL ([c.waudby@ucl.ac.uk](mailto:c.waudby@ucl.ac.uk))
**Licence**: MIT (open source)
**Repository**: [github.com/waudbygroup/topspin-samples](https://github.com/waudbygroup/topspin-samples)
