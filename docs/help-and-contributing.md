# Help and Contributing

## Getting Help

**Email:** [c.waudby@ucl.ac.uk](mailto:c.waudby@ucl.ac.uk)

**GitHub Issues:** [github.com/nmr-samples/topspin/issues](https://github.com/nmr-samples/topspin/issues)

Report bugs or ask questions via GitHub Issues. Include your TopSpin version, operating system, and steps to reproduce any problems.

---

## Contributing

Sample Manager is open source (MIT licence). Contributions from the NMR community are welcome.

### Ways to Contribute

- Report bugs or request features via [GitHub Issues](https://github.com/nmr-samples/topspin/issues)
- Improve documentation by submitting corrections or additions
- Write code to fix bugs or add features
- Propose schema changes in the [nmr-sample-schema](https://github.com/nmr-samples/schema) repository

### Development Setup

To contribute code:

1. Fork the repository on GitHub
2. Clone your fork and configure TopSpin to use your development installation (via `setres`)
3. Create a feature branch
4. Make your changes and test in TopSpin
5. Open a pull request on GitHub

### Code Requirements

- Test with Jython 2.7.2 (TopSpin's embedded Python)
- Avoid Python 3-only syntax
- Use Java Swing components (JavaFX not available)
- Ensure backwards compatibility with existing sample JSON files
- Update documentation if you've added features

### Schema Changes

If you believe there is a need to modify the sample metadata structure, propose changes in the [nmr-sample-schema](https://github.com/nmr-samples/schema) repository. Schema changes require clear use cases, backwards compatibility plans, and updates to all tools in the ecosystem.

---

**Questions?** [Email Chris Waudby](mailto:c.waudby@ucl.ac.uk) or open an issue on GitHub.
