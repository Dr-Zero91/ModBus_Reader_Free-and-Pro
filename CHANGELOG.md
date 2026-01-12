# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-01-12

### Added
- **Server Mode (Simulator)**: Support for Modbus TCP and RTU Slave simulation.
- **Client Monitoring**: Real-time logging of connected clients (IP address) and read/write operations.
- **Licensing System**: 
    - Online activation via PHP/MySQL backend.
    - Hardware locking (Machine ID).
    - Encrypted binary protection using Cython (`.pyd`) for security.
- **Auto-Updater**: Automatic check and notification for new versions.
- **Multiple Sessions**: Ability to open multiple concurrent client connections in separate tabs.
- **Data Recording**: Feature to record register changes over time and save to log files.
- **Installer**: Dedicated `ModbusManager_Setup.exe` for streamlined installation without external dependencies.
- **Manual**: Comprehensive user guide (`Manual.md`) included.

### Changed
- **Performance**: Optimized register refresh rates and UI responsiveness.
- **UI/UX**: Transitioned to a modern Dark Mode interface using `CustomTkinter`.

### Fixed
- Resolved `TypeError` issues during ModbusServerContext initialization.
- Fixed validation logic for manual license entry.
- Corrected various layout issues in the settings panel.

## [1.0.0] - 2025-12-22

### Initial Release
- **Modbus Client**: Connect to Modbus TCP and RTU (Serial) devices.
- **Data Types**: Support for Coils (01), Discrete Inputs (02), Holding Registers (03), and Input Registers (04).
- **Visualization**: tabular view of register values.
- **Management**: 
    - Export and Import register configurations to/from Excel.
    - Custom descriptions for registers.
