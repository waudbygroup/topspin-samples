# Contributing

We welcome contributions from the NMR community! Whether you're reporting bugs, suggesting features, improving documentation, or contributing code, your input helps make Sample Manager better for everyone.

## Ways to Contribute

### Report Bugs

Found a problem? Let us know!

**How to report:**

1. **Check existing issues** - Search [GitHub Issues](https://github.com/waudbygroup/topspin-samples/issues) to see if it's already reported
2. **Create a new issue** - Click "New Issue" and provide:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs. actual behavior
   - Your environment (TopSpin version, Java version, OS)
   - Screenshots if relevant

**Example bug report:**

> **Title:** Timeline not showing 3D experiments
>
> **Description:**
> 3D experiments (PARMODE=2) appear in timeline but not color-coded as green. They show as black (1D) instead.
>
> **Steps to reproduce:**
> 1. Run 3D HNCO experiment
> 2. Open Sample Manager timeline
> 3. Observe experiment color
>
> **Expected:** Green text for 3D experiment
> **Actual:** Black text
>
> **Environment:**
> - TopSpin 4.1.3
> - Java 11.0.20
> - macOS 14.2

### Suggest Features

Have an idea for improvement?

**How to suggest:**

1. **Check existing issues** - Someone may have suggested it already
2. **Create a feature request** - Explain:
   - What problem does it solve?
   - How would it work?
   - Why would it help NMR users?
   - Any examples from other tools?

**Example feature request:**

> **Title:** Add export to CSV function
>
> **Description:**
> It would be useful to export sample metadata to CSV format for analysis in Excel or Python.
>
> **Use case:**
> We run screening experiments with 96 samples. Being able to export all sample metadata to CSV would let us analyze results more easily (correlate NMR data with sample composition).
>
> **Proposed solution:**
> Add "Export CSV" button that creates a CSV file with one row per sample and columns for all metadata fields.

### Improve Documentation

Documentation improvements are always welcome!

**Areas to contribute:**

- Fix typos or unclear explanations
- Add examples or use cases
- Improve beginner-friendliness
- Add screenshots or diagrams
- Translate to other languages

**How to contribute docs:**

1. Fork the repository
2. Edit files in `docs/` directory (Markdown format)
3. Submit a pull request
4. Maintainers will review and merge

### Contribute Code

Want to fix bugs or add features yourself?

**Getting started:**

1. **Fork and clone** the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/topspin-samples.git
   cd topspin-samples
   ```

2. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes** - Edit Python files in `src/`

4. **Test your changes** - Install locally and test in TopSpin

5. **Commit** with clear messages:
   ```bash
   git add .
   git commit -m "Add CSV export functionality"
   ```

6. **Push and create Pull Request**:
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open PR on GitHub

**Code guidelines:**

- **Python 2.7 compatible** - Sample Manager runs in Jython 2.7.2
- **Pure Python only** - No C extensions (Jython limitation)
- **Follow existing style** - Match formatting of existing code
- **Comment your code** - Help others understand your changes
- **Test in TopSpin** - Ensure it works in real TopSpin environment

**Key files:**

- `src/samples.py` - Main GUI application
- `src/ija.py` / `src/eja.py` - Integration commands
- `src/lib/schema_form.py` - Form generation from schema
- `src/lib/sample_io.py` - File I/O operations
- `src/lib/timeline.py` - Timeline parsing logic

### Propose Schema Changes

Want to add or modify metadata fields?

Schema changes go through the **separate schema repository**:

**[nmr-sample-schema](https://github.com/waudbygroup/nmr-sample-schema)**

**Process:**

1. Open issue in schema repository
2. Describe proposed change:
   - What field(s) to add/modify?
   - What problem does it solve?
   - What data type and allowed values?
   - Any examples?
3. Community discussion
4. Schema maintainers implement and version
5. Sample Manager automatically picks up changes

**Example schema proposal:**

> **Title:** Add temperature field
>
> **Description:**
> Add field to record sample temperature during experiments.
>
> **Proposed field:**
> ```json
> "temperature": {
>   "title": "Temperature (K)",
>   "type": "number",
>   "minimum": 0,
>   "description": "Sample temperature in Kelvin"
> }
> ```
>
> **Rationale:**
> Temperature is a critical experimental parameter. Currently users put this in Notes, but structured field would enable searching/filtering by temperature.

## Community Guidelines

### Be Respectful

- Treat everyone with respect and kindness
- Welcome newcomers and help them learn
- Provide constructive feedback
- Disagree professionally

### Be Clear

- Use clear, descriptive titles for issues/PRs
- Provide enough detail for others to understand
- Include examples when possible
- Ask questions if something is unclear

### Be Patient

- Maintainers are volunteers with limited time
- Response may take days or weeks
- Complex changes require discussion and review
- Not all suggestions can be implemented

## Getting Help

### Questions About Using Sample Manager

- Check the [documentation](guide/usage.md)
- Search [existing issues](https://github.com/waudbygroup/topspin-samples/issues)
- Open a new issue with "Question:" prefix
- Email Chris Waudby: [c.waudby@ucl.ac.uk](mailto:c.waudby@ucl.ac.uk)

### Questions About Development

- Check [CLAUDE.md](https://github.com/waudbygroup/topspin-samples/blob/main/CLAUDE.md) for architecture details
- Open an issue asking for clarification
- Propose improvements to development documentation

### Questions About TopSpin Integration

- Refer to TopSpin Python/Jython documentation
- Ask in TopSpin user forums
- Share your findings with the Sample Manager community

## Recognition

All contributors are valued and appreciated!

- Contributors will be acknowledged in release notes
- Significant contributions acknowledged in README
- Code contributions tracked via GitHub

## Contact

**Project Maintainer:**

- **Chris Waudby**
- Email: [c.waudby@ucl.ac.uk](mailto:c.waudby@ucl.ac.uk)
- GitHub: [@chriswaudby](https://github.com/chriswaudby)
- Institution: University College London

**Project Links:**

- **Main Repository:** [github.com/waudbygroup/topspin-samples](https://github.com/waudbygroup/topspin-samples)
- **Schema Repository:** [github.com/waudbygroup/nmr-sample-schema](https://github.com/waudbygroup/nmr-sample-schema)
- **Web Viewer:** [github.com/waudbygroup/nmr-sample-viewer](https://github.com/waudbygroup/nmr-sample-viewer)
- **Issues:** [github.com/waudbygroup/topspin-samples/issues](https://github.com/waudbygroup/topspin-samples/issues)

## License

Sample Manager is open source software. Check the repository for license details.

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for helping improve Sample Manager for the NMR community!
