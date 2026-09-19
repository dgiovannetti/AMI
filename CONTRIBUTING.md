# Contributing to AMI

Thank you for considering contributing to AMI! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Relevant log files (`ami_log.csv`)

### Suggesting Features

Feature suggestions are welcome! Please include:
- Clear description of the feature
- Use case / motivation
- Proposed implementation (optional)

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Commit with clear messages (`git commit -m 'Add amazing feature'`)
7. Push to your fork (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 💻 Development Setup

Active development is **AMI 3.x** in `3.0/` (Python 3.10+). The root `src/` tree is the frozen 2.x line; do not add features there.

```bash
git clone https://github.com/YOUR_USERNAME/AMI.git
cd AMI/3.0

pip install -r requirements.txt
pip install pytest

# Run
python run.py

# Tests
PYTHONPATH=src python -m pytest
```

## 🏗️ Project Structure

```
AMI/
├── 3.0/                      # Current product (v3.x)
│   ├── src/ami/
│   │   ├── core/             # config, paths, models
│   │   ├── services/         # monitor, logger, API, updater
│   │   └── ui/               # tray, dashboard, settings
│   ├── tests/
│   ├── config.json
│   └── resources/
└── src/                      # Legacy 2.x (do not extend)
```

## 📝 Coding Standards

### Python Style
- Follow PEP 8
- Use type hints where appropriate
- Document functions with docstrings
- Maximum line length: 100 characters

### Commits
- Use clear, descriptive commit messages
- Reference issues when applicable (#123)
- Keep commits focused and atomic

### Documentation
- Update README.md for user-facing changes
- Update docstrings for code changes
- Add comments for complex logic
- **Release notes and public docs**: always provide **English + Italian** (EN/IT)

## 🧪 Testing

Before submitting a PR:
1. Run `PYTHONPATH=src python -m pytest` from `3.0/`
2. Test the application manually (`python run.py`)
3. Verify tray menu, dashboard, and notifications
4. Verify logs are created correctly
5. Build the executable and test it if you touched packaging

## 📋 Code Review Process

1. All PRs require review before merging
2. Address reviewer feedback promptly
3. Keep discussions professional and constructive
4. Be patient - reviews may take time

## 🎯 Priority Areas

Current areas where contributions are especially welcome:
- **Classifier accuracy** - Captive portal, proxy, and LAN-only cases
- **Tests** - API, updater, and UI smoke coverage
- **Localization** - Add support for multiple languages
- **Linux packaging** - CI currently builds Windows and macOS only

## 📄 License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## 💬 Questions?

Feel free to open an issue with the "question" label if you need help or clarification.

---

Thank you for contributing to AMI! 🎉
