# Help and Contributing

## Getting Help

### Common Issues

**"Command not found when I type `samples`"**

Check that the installation path is correctly configured in TopSpin:

1. Type `setres` in TopSpin
2. Navigate to **Directories** → **Manage source directories for edpul, edau, etc.**
3. Select the **Jython Programs** tab
4. Verify the path points to `[...]/topspin-samples/src` (the `src` subdirectory, not the repository root)
5. Restart TopSpin after making changes

**"Schema version X.X.X not found"**

This means a sample was created with a schema version that's not installed on your system. Update your installation:

```bash
cd /path/to/topspin-samples
git pull
```

Then restart TopSpin.

**"Multiple windows opening when I type `samples`"**

This should not happen - Sample Manager uses a singleton pattern. If you see this behaviour:

1. Close all Sample Manager windows
2. Restart TopSpin
3. If the problem persists, [report it as a bug](#reporting-bugs)

**"Cannot edit sample - form is read-only"**

Samples open in read-only mode by default. To edit:

- Double-click the sample in the list, or
- Select the sample and click the "Edit" button

The form will switch to edit mode with enabled fields.

### Reporting Bugs

If you encounter a bug, please report it via [GitHub Issues](https://github.com/waudbygroup/topspin-samples/issues).

**Include the following information:**

- TopSpin version
- Operating system
- Sample Manager version (check with `git log -1` in the installation directory)
- Error message (if any)
- Steps to reproduce the problem
- Screenshots if relevant

**Example bug report:**

```
Title: Timeline view crashes when opening directory with >1000 experiments

Environment:
- TopSpin 4.2.0
- macOS 14.0
- Sample Manager commit: abc1234

Steps to reproduce:
1. Type `samples` in TopSpin
2. Browse to directory /data/large-project (contains 1500 experiments)
3. Click Timeline tab

Expected: Timeline displays all experiments
Actual: Window freezes and becomes unresponsive

Screenshot attached.
```

### Getting Support

**Email:** [c.waudby@ucl.ac.uk](mailto:c.waudby@ucl.ac.uk)

Contact Chris Waudby for:

- Questions about installation or usage
- Feedback on features or workflow
- Discussion of scientific applications

**GitHub Discussions:** [github.com/waudbygroup/topspin-samples/discussions](https://github.com/waudbygroup/topspin-samples/discussions)

Use GitHub Discussions for:

- General questions about the tool
- Sharing tips and workflows
- Requesting new features
- Community support

---

## Contributing

We welcome contributions from the NMR community. Sample Manager is open source (MIT licence) and designed to be extensible.

### Ways to Contribute

**Report bugs or request features** via [GitHub Issues](https://github.com/waudbygroup/topspin-samples/issues).

**Improve documentation** by submitting corrections or additions to the docs (this website).

**Write code** to fix bugs or add features. See the development section below.

**Share workflows** in GitHub Discussions to help other users adopt the tool.

**Propose schema changes** in the [nmr-sample-schema](https://github.com/waudbygroup/nmr-sample-schema) repository if you need additional fields or data structures.

### Development Setup

To contribute code:

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/topspin-samples.git
   cd topspin-samples
   ```

3. **Configure TopSpin** to use your development installation:
   - Type `setres` in TopSpin
   - Add the path to your cloned `src/` directory
   - Restart TopSpin

4. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```

5. **Make your changes** and test in TopSpin

6. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

7. **Push to your fork**:
   ```bash
   git push origin feature/my-new-feature
   ```

8. **Open a pull request** on GitHub

### Code Style

**Python code:**

- Follow PEP 8 style guidelines
- Use descriptive variable names
- Add docstrings to functions and classes
- Comment complex logic

**Jython compatibility:**

- Test with Jython 2.7.2 (TopSpin's embedded Python)
- Avoid Python 3-only syntax
- Use only standard library and Java libraries (no C extensions)

**GUI code:**

- Use Java Swing components (JavaFX not available)
- Follow existing patterns for dialogs and forms
- Test on multiple operating systems if possible

### Testing

Sample Manager does not have automated tests (Jython testing infrastructure is complex). Manual testing is required:

1. Test in a real TopSpin environment
2. Test with sample datasets
3. Verify backwards compatibility with old sample JSON files
4. Check the timeline view with directories containing many experiments
5. Test on multiple operating systems if possible

### Pull Request Guidelines

**Before submitting:**

- Test your changes thoroughly in TopSpin
- Ensure backwards compatibility with existing sample files
- Update documentation if you've added features
- Add clear commit messages explaining your changes

**Pull request description should include:**

- What problem does this solve?
- What changes did you make?
- How did you test it?
- Any breaking changes or migration steps needed?

### Schema Changes

If you need to modify the sample metadata structure (add fields, change validation rules, etc.), propose changes in the [nmr-sample-schema](https://github.com/waudbygroup/nmr-sample-schema) repository first.

Schema changes require:

- Clear use case and justification
- Backwards compatibility plan
- Version number increment following semantic versioning
- Updates to all tools in the ecosystem

### Community Guidelines

- Be respectful and constructive in discussions
- Focus on scientific applications and practical workflows
- Help other users when you can
- Share your experiences and use cases

---

**Questions about contributing?** [Email Chris Waudby](mailto:c.waudby@ucl.ac.uk) or open a discussion on GitHub.
