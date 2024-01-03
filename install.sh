#!/bin/bash

# Check if Python and pip are installed
if ! command -v python3 > /dev/null || ! command -v pip3 > /dev/null; then
    echo "Error: Python and pip are required. Please install them before running this script."
    exit 1
fi

# Install specific Python packages (excluding pywin32 on non-Windows systems)
if [[ $(uname) == "Linux" ]]; then
    pip3 install speechrecognition==3.10.0 pyttsx3==2.90
else
    pip3 install speechrecognition==3.10.0 pyttsx3==2.90 pywin32==306
fi

echo "Installation completed successfully."
