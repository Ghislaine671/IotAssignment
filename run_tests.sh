#!/bin/bash
# ============================================
#  Run Unit Tests
# ============================================

echo "=== Running Unit Tests ==="
echo ""
./venv/bin/python -m pytest tests/ -v
