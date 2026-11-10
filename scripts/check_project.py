"""Запускает тесты и сохраняет проверяемый протокол для документации."""
import io
import json
import os
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
              failures=len(result.failures),errors=len(result.errors),tests=result.records)
    (ROOT/'docs/test_results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    lines=['# Протокол проверки проекта','',f'Дата: {data["date"]}', '',
           f'Выполнено {result.testsRun} тестов; ошибок {len(result.errors)}; непройденных {len(result.failures)}.',
           '', 'Команда: `python scripts/check_project.py`.', '',
           'Проверки выполняются на временных SQLite-базах и копии исходной базы. Рабочая база не изменяется.', '',
           '| Проверка | Результат |', '|---|---|']
    lines += [f'| `{r["test"]}` | {r["status"]} |' for r in result.records]
    lines += ['', 'Проверены сервисы и запуск Qt в режиме offscreen. PostgreSQL-сервер и работа на Windows/macOS в этом прогоне не проверялись.', '', '```text',log.strip(),'```','']
    (ROOT/'docs/TEST_REPORT.md').write_text('\n'.join(lines))
    sys.exit(not result.wasSuccessful())
