# Changelog

All notable changes to AMI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-10

### Added
- Initial release of AMI (Active Monitor of Internet)
- System tray application with status indicators (green/yellow/red)
- Multi-host ping testing with parallel execution
- HTTP connectivity verification
- Local network detection
- Real-time status monitoring with configurable polling interval
- Windows toast notifications for connection state changes
- CSV event logging with automatic rotation
- Interactive dashboard with statistics and graphs
- Connection history visualization
- Uptime tracking and statistics
- Manual connection testing
- Configurable thresholds for unstable connection detection
- Optional HTTP API server for programmatic status queries
- Auto-start functionality for Windows
- Build script for creating standalone executable
- Icon generation tools
- Comprehensive configuration via JSON file

### Features
- **Network Monitoring**
  - Parallel ping testing to multiple hosts
  - HTTP connectivity verification (Google generate_204)
  - Local network vs internet distinction
  - Configurable timeout and retry logic
  
- **User Interface**
  - System tray icon with color-coded status
  - Context menu with quick actions
  - Detailed dashboard with real-time graphs
  - Tooltip with status summary
  
- **Notifications**
  - Windows toast notifications
  - Configurable notification triggers
  - Silent mode option
  
- **Logging & Analytics**
  - CSV event logging
  - Automatic log rotation
  - Uptime percentage tracking
  - Latency statistics
  - Connection history graphs
  
- **Advanced**
  - Optional HTTP API (localhost:7212)
  - Windows auto-start support
  - Customizable test hosts
  - Adjustable polling intervals
  - Stability thresholds configuration

### Technical
- Built with Python 3.8+ and PyQt6
- Cross-platform design (optimized for Windows)
- Async network operations with threading
- Minimal resource usage
- Standalone executable support via PyInstaller

## [Unreleased]

### Planned Features
- Settings GUI (currently config.json only)
- Telegram bot integration for remote alerts
- Dark/Light theme switching
- Network speed testing
- VPN detection
- Custom notification sounds
- System tray icon animation during tests
- Export statistics to CSV/JSON
- Network outage report generation
- Multiple network profile support
