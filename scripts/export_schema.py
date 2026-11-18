"""Сохраняет фактическую спецификацию ORM для пояснительной записки."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from database.models import Base
schema=[]
for table in Base.metadata.sorted_tables:
    schema.append({'name':table.name,'columns':[{'name':c.name,'type':str(c.type),'nullable':c.nullable,
        'primary_key':c.primary_key,'unique':bool(c.unique),'foreign_key':','.join(f.target_fullname for f in c.foreign_keys)} for c in table.columns]})
(ROOT/'docs/schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2),encoding='utf-8')
