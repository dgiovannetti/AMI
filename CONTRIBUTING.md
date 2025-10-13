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

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/AMI.git
cd AMI

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-build.txt

# Run in development mode
python AMI.py
```

## 🏗️ Project Structure

```
AMI/
├── src/              # Source code
│   ├── tray_app.py       # Main application
│   ├── network_monitor.py # Network monitoring
│   ├── dashboard.py       # Dashboard UI
│   ├── logger.py          # Event logging
│   ├── notifier.py        # Notifications
│   └── api_server.py      # HTTP API
├── tools/            # Build and utility tools
├── resources/        # Icons and assets
└── config.json       # Configuration
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

## 🧪 Testing

Before submitting a PR:
1. Test the application manually
2. Verify all menu items work
3. Check dashboard displays correctly
4. Test notifications
5. Verify logs are created correctly
6. Build the executable and test it

## 📋 Code Review Process

1. All PRs require review before merging
2. Address reviewer feedback promptly
3. Keep discussions professional and constructive
4. Be patient - reviews may take time

## 🎯 Priority Areas

Current areas where contributions are especially welcome:
- **Settings GUI** - Replace config.json editing with a proper UI
- **Dark/Light Theme** - Implement automatic theme switching
- **Network Speed Tests** - Add bandwidth testing
- **Localization** - Add support for multiple languages
- **macOS/Linux Support** - Improve cross-platform compatibility
- **Unit Tests** - Add comprehensive test coverage

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 💬 Questions?

Feel free to open an issue with the "question" label if you need help or clarification.

---

Thank you for contributing to AMI! 🎉
