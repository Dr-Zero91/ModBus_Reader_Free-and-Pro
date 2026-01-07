import PyInstaller.__main__
import os

# Build the main application
try:
    print("Building Modbus Reader Pro...")
    PyInstaller.__main__.run([
        'modbus_reader.py',
        '--onefile',
        '--noconsole',
        '--name=ModbusReaderPro',
        '--hidden-import=babel.numbers',
        '--clean'
    ])
    print("Build Complete! Check the 'dist' folder.")
except Exception as e:
    print(f"Error building main app: {e}")

# Build the keygen (optional, for admin)
try:
    print("Building KeyGen...")
    PyInstaller.__main__.run([
        'keygen.py',
        '--onefile',
        '--name=ModbusKeyGen',
        '--clean'
    ])
    print("KeyGen Build Complete!")
except Exception as e:
    print(f"Error building keygen: {e}")
