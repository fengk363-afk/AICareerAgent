#!/bin/bash
# 运行测试
set -e

cd backend
source venv/bin/activate 2>/dev/null || true
pip install -q pytest pytest-asyncio 2>/dev/null || true
PYTHONPATH=. pytest tests/ -v --tb=short
