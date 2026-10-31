# apps/seo/legacy_csv.py — чтение docs/data/redirects.csv
"""Разбор таблицы адресов старого сайта (разделитель «;», первая строка — заголовки, кодировка с BOM)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LegacyRow:
    """Строка таблицы: старый адрес, новый адрес, действие (keep/301/410/canonical), тип, комментарий."""

    old_path: str
    new_path: str
    action: str
    kind: str
    note: str

    @property
    def is_pattern(self) -> bool:
        """Правило с «*» или по хосту — реализовано кодом, а не строкой таблицы."""
        return "*" in self.old_path or not self.old_path.startswith("/")


def read_rows(path: Path) -> list[LegacyRow]:
    """
    Args:
        path: путь к redirects.csv.

    Returns:
        Все строки таблицы.
    """
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        return [
            LegacyRow(
                old_path=(r.get("old_path") or "").strip(),
                new_path=(r.get("new_path") or "").strip(),
                action=(r.get("action") or "").strip(),
                kind=(r.get("type") or "").strip(),
                note=(r.get("note") or "").strip().replace("\n", " ")[:300],
            )
            for r in reader
            if r.get("old_path")
        ]
