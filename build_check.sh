#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "================================"
echo "      VIN09.3 FULL BUILD CHECK"
echo "================================"
python -m py_compile main.py brain/*.py brain/reasoning/*.py memory/*.py tools/*.py learning/*.py security/*.py tests/*.py
echo "================================"
echo "       VIN09.3 BUILD PASSED"
echo "================================"
echo "Start with: python main.py"
