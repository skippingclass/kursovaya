"""Запускает тесты и сохраняет проверяемый протокол для документации."""
import io
import json
import os
import platform
import sys
import unittest
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

class Result(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs); self.records=[]
    def addSuccess(self,test):
        super().addSuccess(test); self.records.append({'test':test.id(),'status':'passed'})
    def addFailure(self,test,err):
        super().addFailure(test,err); self.records.append({'test':test.id(),'status':'failed'})
    def addError(self,test,err):
        super().addError(test,err); self.records.append({'test':test.id(),'status':'error'})

if __name__=='__main__':
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite)
    log=stream.getvalue(); print(log)
    data=dict(date=datetime.now().isoformat(timespec='seconds'),total=result.testsRun,
              platform=platform.system(), failures=len(result.failures),errors=len(result.errors),tests=result.records)
    (ROOT/'docs/test_results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Протокол проверки проекта','',f'Дата: {data["date"]}', '',
           f'Выполнено {result.testsRun} тестов; ошибок {len(result.errors)}; непройденных {len(result.failures)}.',
           '', 'Команда: `python scripts/check_project.py`.', '',
           'Проверки выполняются на временных SQLite-базах, включая отдельную модель прежней схемы.', '',
           '| Проверка | Результат |', '|---|---|']
    lines += [f'| `{r["test"]}` | {r["status"]} |' for r in result.records]
    lines += ['', f'Проверены HTTP API, сервисы и интерфейсы Qt в режиме offscreen. Прогон выполнен на {data["platform"]} и SQLite.', '', '```text',log.strip(),'```','']
    (ROOT/'docs/TEST_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    sys.exit(not result.wasSuccessful())
