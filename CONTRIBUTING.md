# Contributing to GhostOps ⚡

Thank you for your interest in contributing to GhostOps! We are building the next-generation autonomous terminal SRE for Linux and Cloud engineers worldwide.

## Code of Conduct
Please be respectful, collaborative, and constructive in all discussions, pull requests, and issues.

## Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/EngJoDev/ghostops.git
   cd ghostops
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install editable package with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Run unit tests to verify setup:
   ```bash
   python3 -m unittest discover tests
   ```

## Pull Request Guidelines
- Ensure all tests pass.
- Write unit tests for any new collectors or safety heuristics.
- Keep terminal UI clean, responsive, and compatible with standard ANSI/xterm terminals.
- Follow PEP 8 standards.

Thank you for making GhostOps better! 🚀

