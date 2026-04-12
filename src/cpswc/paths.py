"""
paths.py — CPSWC 项目路径解析

所有模块通过此文件获取 registries/samples/governance 等目录路径,
不再硬编码 SPECS_DIR 或使用 sys.path hack。
"""
from pathlib import Path

# Project root = directory containing pyproject.toml
# Walk up from this file: src/cpswc/paths.py → src/cpswc/ → src/ → CPSWC/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

REGISTRIES_DIR = PROJECT_ROOT / "registries"
RESERVED_DIR = REGISTRIES_DIR / "reserved"
SAMPLES_DIR = PROJECT_ROOT / "samples"
GOVERNANCE_DIR = PROJECT_ROOT / "governance"
DOCS_DIR = PROJECT_ROOT / "docs"
TESTS_DIR = PROJECT_ROOT / "tests"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
