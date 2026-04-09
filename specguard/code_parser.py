"""Parse Python files to extract configuration-like constants."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def _normalize_key(name: str) -> str:
    return name.strip().lower()


def _literal_value(node: ast.AST) -> Any | None:
    """Return literal values that are safe to compare in docs."""
    try:
        value = ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return None
    if isinstance(value, (int, float, str, bool)):
        return value
    return None


def _env_default(node: ast.AST) -> Any | None:
    """Extract default values from os.getenv calls."""
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return None
    if node.func.attr != "getenv":
        return None
    if not isinstance(node.func.value, ast.Name) or node.func.value.id != "os":
        return None
    if len(node.args) < 2:
        return None
    return _literal_value(node.args[1])


def _dict_entries(node: ast.AST) -> dict[str, Any]:
    """Extract simple literal entries from dict expressions."""
    if not isinstance(node, ast.Dict):
        return {}
    extracted: dict[str, Any] = {}
    for key_node, value_node in zip(node.keys, node.values):
        if key_node is None:
            continue
        key_value = _literal_value(key_node)
        value = _literal_value(value_node) or _env_default(value_node)
        if isinstance(key_value, str) and value is not None:
            extracted[_normalize_key(key_value)] = value
    return extracted


def _source_line(lines: list[str], line_number: int) -> str:
    if 1 <= line_number <= len(lines):
        return lines[line_number - 1].strip()
    return ""


class ConstantCollector(ast.NodeVisitor):
    """Collect constants, config defaults, and config-like class attributes."""

    def __init__(self, path: Path, source_lines: list[str]) -> None:
        self.path = path
        self.source_lines = source_lines
        self.constants: dict[str, dict[str, Any]] = {}
        self.class_context: list[bool] = []

    def _store(self, key: str, value: Any, line_number: int) -> None:
        self.constants[key] = {
            "value": value,
            "source_file": str(self.path),
            "line": line_number,
            "context": _source_line(self.source_lines, line_number),
        }

    def _capture_name(self, name: str, value_node: ast.AST, line_number: int, allow_public: bool = False) -> None:
        value = _literal_value(value_node)
        if value is None:
            value = _env_default(value_node)

        is_config_container = name.isupper() or name.lower() in {"settings", "config", "defaults"}
        dict_values = _dict_entries(value_node) if is_config_container or allow_public else {}
        for nested_key, nested_value in dict_values.items():
            self._store(nested_key, nested_value, line_number)

        if value is None:
            return

        if name.isupper() or (allow_public and not name.startswith("_")):
            self._store(_normalize_key(name), value, line_number)

    def visit_Assign(self, node: ast.Assign) -> None:
        allow_public = bool(self.class_context and self.class_context[-1])
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._capture_name(target.id, node.value, node.lineno, allow_public=allow_public)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is None or not isinstance(node.target, ast.Name):
            return
        allow_public = bool(self.class_context and self.class_context[-1])
        self._capture_name(node.target.id, node.value, node.lineno, allow_public=allow_public)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        base_names = {
            base.id
            for base in node.bases
            if isinstance(base, ast.Name)
        }
        decorator_names = {
            decorator.id
            for decorator in node.decorator_list
            if isinstance(decorator, ast.Name)
        }
        is_config_like = any(
            token in base_names | decorator_names
            for token in {"BaseSettings", "dataclass", "Config"}
        ) or node.name.lower().endswith(("config", "settings"))

        self.class_context.append(is_config_like)
        self.generic_visit(node)
        self.class_context.pop()


def parse_python_file(file_path: str | Path) -> dict[str, dict[str, Any]]:
    """Extract constants and config defaults from a Python file."""
    path = Path(file_path)
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return {}

    collector = ConstantCollector(path, source.splitlines())
    collector.visit(tree)
    return collector.constants


def parse_python_path(path: str | Path) -> dict[str, dict[str, Any]]:
    """Parse a file or directory, aggregating constants across Python files."""
    target = Path(path)
    if target.is_file():
        return parse_python_file(target)

    constants: dict[str, dict[str, Any]] = {}
    for file_path in sorted(target.rglob("*.py")):
        constants.update(parse_python_file(file_path))
    return constants
