# -*- coding: utf-8 -*-
"""预处理层单元测试：标识符归一 + 注释去除。"""
from src.preprocessor.ast_normalizer import normalize


def test_identifier_normalization():
    skeleton = normalize("def foo(x):\n    return x + 1\n")
    assert "foo" not in skeleton
    assert "FUNC_" in skeleton
    assert "VAR_" in skeleton


def test_comment_removal():
    skeleton = normalize("x = 1  # 这是个注释\n")
    assert "注释" not in skeleton
    assert "x" not in skeleton  # x 会被归一为 VAR_n


def test_empty_code():
    assert normalize("") == ""


def test_function_name_normalized():
    skeleton = normalize("def calculate_interest(principal, rate, time):\n    return principal\n")
    assert "calculate_interest" not in skeleton
    assert "FUNC_0" in skeleton
