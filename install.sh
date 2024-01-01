#!/bin/bash

# Check if Python and pip are installed
if ! command -v python3 > /dev/null || ! command -v pip3 > /dev/null; then
    echo "Error: Python and pip are required. Please install them before running this script."
    exit 1
fi

# Install specific Python packages
pip3 install speechrecognition pyttsx3 pywin32

# Assuming mood is your custom module and is not available on PyPI
# If mood is available on PyPI, you can install it using pip3 as well
# Example: pip3 install mood

echo "Installation completed successfully."

