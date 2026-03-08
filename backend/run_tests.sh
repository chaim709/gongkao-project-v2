#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "========== 运行单元测试 =========="
pytest tests/unit -v -m unit

echo ""
echo "========== 运行集成测试 =========="
pytest tests/integration -v -m integration

echo ""
echo "========== 生成覆盖率报告 =========="
pytest tests/ --cov=app --cov-report=html --cov-report=term

echo ""
echo "覆盖率报告已生成: htmlcov/index.html"
