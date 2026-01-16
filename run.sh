#!/bin/bash
# Quick run script for Linux/Mac - Auto setup and run

echo "Starting Acx Shell..."
python3 main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Setup failed! Please check the errors above."
    exit 1
fi
