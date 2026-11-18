@echo off
setlocal
chcp 65001 >nul
pushd "%~dp0" || exit /b 1
set "APP_PYTHON=runtime\python.exe"
if exist "%APP_PYTHON%" goto launch

set "APP_PYTHON=.venv\Scripts\python.exe"
if exist "%APP_PYTHON%" goto dependencies

echo Подготовка Python для первого запуска...
where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>nul
if errorlevel 1 goto try_python
py -3 -m venv .venv
if errorlevel 1 goto setup_failed
goto dependencies

:try_python
where python >nul 2>nul
if errorlevel 1 goto no_python
python -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>nul
if errorlevel 1 goto no_python
python -m venv .venv
if errorlevel 1 goto setup_failed

:dependencies
if not exist ".venv\requirements.installed" goto install
fc /b requirements.txt ".venv\requirements.installed" >nul 2>nul
if not errorlevel 1 goto launch

:install
echo Установка зависимостей. При первом запуске нужен интернет.
"%APP_PYTHON%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto setup_failed
copy /y requirements.txt ".venv\requirements.installed" >nul
if errorlevel 1 goto setup_failed

:launch
if /i "%~1"=="--check" goto check
if /i "%~1"=="--network" goto network
"%APP_PYTHON%" -B run.py
goto finished

:network
"%APP_PYTHON%" -B -m scripts.run_network
goto finished

:check
"%APP_PYTHON%" -B -c "import run, run_client, openpyxl, reportlab, psycopg2; from server.api import app; print('OK')"

:finished
set "APP_EXIT=%errorlevel%"
if "%APP_EXIT%"=="0" goto end
echo Запуск завершился с ошибкой.
if /i not "%~1"=="--check" pause
goto end

:no_python
echo Установите Python 3.14 с https://www.python.org/downloads/windows/
echo После установки снова откройте run.bat.
goto failed

:setup_failed
echo Подготовка приложения не завершилась. Проверьте сообщение выше и повторите запуск.

:failed
set "APP_EXIT=1"
if /i not "%~1"=="--check" pause

:end
popd
exit /b %APP_EXIT%
