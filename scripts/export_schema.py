"""Сохраняет фактическую спецификацию ORM для пояснительной записки."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from database.models import Base
from sqlalchemy import CheckConstraint, UniqueConstraint


def export_schema():
    schema = []
    for table in Base.metadata.sorted_tables:
        columns = []
        for column in table.columns:
            default = column.default
            columns.append({
                "name": column.name,
                "type": str(column.type),
                "nullable": column.nullable,
                "primary_key": column.primary_key,
                "unique": bool(column.unique),
                "foreign_key": ",".join(sorted(key.target_fullname for key in column.foreign_keys)),
                "default": default.arg if default is not None and default.is_scalar else None,
            })
        schema.append({
            "name": table.name,
            "columns": columns,
            "unique_constraints": sorted(
                [column.name for column in constraint.columns]
                for constraint in table.constraints if isinstance(constraint, UniqueConstraint)
            ),
            "check_constraints": sorted(
                str(constraint.sqltext)
                for constraint in table.constraints if isinstance(constraint, CheckConstraint)
            ),
        })
    return schema


if __name__ == "__main__":
    target = ROOT / "docs/schema.json"
    target.write_text(json.dumps(export_schema(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
