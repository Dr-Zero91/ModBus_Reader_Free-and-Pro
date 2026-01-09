# Modbus Manager v1.1

![Version](https://img.shields.io/badge/version-1.1-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/Python-3.14-yellow.svg)

**Modbus Manager** works as a powerful Modbus TCP/RTU Client and Server simulator. Designed for industrial automation engineers, it allows you to test, debug, and monitor Modbus networks with ease.

## 🚀 Features

### Core Features (Free)
*   **Modbus Client (Master)**: Connect to Modbus TCP and RTU (Serial) devices.
*   **Data Visualization**: View registers in a clean, tabular format.
*   **Read/Write**: Support for Coils, Discrete Inputs, Holding Registers, and Input Registers.
*   **Descriptions**: Add custom descriptions to registers for better context.
*   **Excel Integration**: Export and Import register data/descriptions.

### Pro Features
*   **desktop-class UI**: Modern Dark Mode interface based on `CustomTkinter`.
*   **Server Mode (Simulator)**: Turn your PC into a Modbus TCP or RTU Slave device.
    *   Simulate register values and monitor incoming client connections.
    *   View real-time operation logs (Reads/Writes from clients).
*   **Multiple Sessions**: Open multiple client connection tabs simultaneously.
*   **Recording & Playback**: Record register changes over time and replay them.
*   **Auto-Updater**: Automatically checks for and installs new versions.

## 🛡️ Security
This project implements robust security measures for the Pro edition:
*   **Online Activation**: Verifies license keys against a secure PHP/MySQL backend.
*   **Binary Protection**: Core security logic is compiled to machine code (Cython `.pyd`) to prevent tampering.
*   **Anti-Replay & NTP Checks**: Prevents system clock manipulation to bypass trial/license expiry.
*   **Hardware Locking**: Licenses are locked to the specific hardware ID of the PC.

## 🛠️ Installation

### Using the Installer (Recommended)
Download the latest `ModbusManager_v1.1_Setup.exe` from the releases page and follow the wizard.

### Running from Source
1.  Clone the repository:
    ```bash
    git clone https://github.com/RecodeStudio/ModbusManager.git
    cd ModbusManager
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the application:
    ```bash
    python modbus_reader.py
    ```
    *Note: Some Pro features requiring the compiled `protection` module may not be available in source mode unless the `.pyd` is present.*

## 🔧 Architecture
*   **Frontend**: Python + CustomTkinter
*   **Backend**: Pymodbus (Sync/Async)
*   **License Server**: PHP + MySQL
*   **Management**: KeyGen Manager (Admin tool for license generation)

## 📦 Build Instructions
To build the standalone executable:
1.  Ensure you have `PyInstaller` and `Cython` installed.
2.  Compile the protection module:
    ```bash
    python setup_protection.py build_ext --inplace
    ```
3.  Build the EXE:
    ```bash
    python -m PyInstaller ModbusManager.spec
    ```
4.  (Optional) Create Installer: Use Inno Setup with `ModbusManager_Setup.iss`.

## © Credits
Developed by **Renato Cultrera** (Recode Studio).

---

## ⚖️ Legal & Privacy

### Privacy Policy (GDPR Compliance)
**Data Collection:** To validate licenses, we collect the **Machine ID**, **Computer Name**, and **IP Address**.
**Usage:** This data is used **exclusively** for license verification and is **NOT** shared with third parties.
**Your Rights:** To request data deletion (license deactivation), contact `info@recodestudio.it`.

### Terms of Use & Liability
**"As Is" Warranty:** The software is provided "as is" without warranty of any kind.
**Liability:** **Recode Studio is not responsible** for any damage to equipment, data loss, or downtime resulting from the use of this software in industrial environments. The user assumes full responsibility for testing before production use.

