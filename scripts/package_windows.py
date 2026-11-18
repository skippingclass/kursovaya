"""Build the portable Windows x64 archive from a Git checkout or source ZIP."""
import argparse
from hashlib import sha256
from pathlib import Path
from shutil import copy2, copytree, ignore_patterns
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
PYTHON_VERSION = "3.14.9"
PYTHON_SHA256 = "3c01d7cfc666f746a6f064f60fb2156ab0ec464d3d738ab796371a46a9bb24a2"
BUNDLE = "CollegeTeachers"
PUBLISHED_DOCS = (
    "Пояснительная_записка.docx", "Пояснительная_записка.pdf",
    "Презентация_для_защиты.pptx", "Руководство_пользователя.pdf",
    "Руководство_разработчика.pdf", "Требования_к_ПО.pdf",
    "Защита.md", "TEST_REPORT.md", "API.md", "openapi.json",
    "reference/Методические_указания.pdf",
)
START_HERE = """УЧЕТ ПРЕПОДАВАТЕЛЕЙ И УЧЕБНОЙ НАГРУЗКИ
Курсовой проект · Евполов Владислав · П-24-67Б

1. Извлеките весь архив в папку, в которой можно создавать файлы.
2. Откройте папку CollegeTeachers и дважды щёлкните run.bat.
3. Для проверки войдите под логином operator и паролем operator123.
   Для просмотра без изменений войдите как methodist / methodist123.

Программа рассчитана на Windows 10/11 x64. Python и библиотеки входят в архив.
Для первого запуска интернет не требуется. База создаётся в папке data.

Файл run-network.bat открывает клиент и запускает локальный сервер.
Сетевой режим сохраняет демонстрационные записи в отдельной базе.
В папке docs лежат пояснительная записка, презентация, руководства
и сценарий проверки (Защита.md).
"""


def prepare_runtime(bundle, python_archive):
    runtime = bundle / "runtime"
    payload = python_archive.read_bytes()
    if sha256(payload).hexdigest() != PYTHON_SHA256:
        raise ValueError("Контрольная сумма дистрибутива Python не совпала.")
    with ZipFile(python_archive) as package:
        package.extractall(runtime)

    version = ".".join(PYTHON_VERSION.split(".")[:2])
    compact = version.replace(".", "")
    (runtime / f"python{compact}._pth").write_text(
        f"python{compact}.zip\n.\nLib\\site-packages\n..\nimport site\n",
        encoding="ascii", newline="\r\n",
    )
    site_packages = runtime / "Lib" / "site-packages"
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
         "--platform", "win_amd64", "--python-version", version, "--implementation", "cp",
         "--only-binary=:all:", "--no-compile", "--target", str(site_packages),
         "-r", str(ROOT / "requirements.txt"), "colorama"],
        check=True,
    )


def prepare_project(bundle):
    ignore = ignore_patterns("__pycache__", "*.py[cod]")
    for name in ("assets", "database", "services", "server", "ui"):
        copytree(ROOT / name, bundle / name, ignore=ignore)
    for name in ("config.py", "requirements.txt", "run.py", "run_client.py", "run.bat", "run-network.bat"):
        copy2(ROOT / name, bundle / name)
    (bundle / "scripts").mkdir()
    copy2(ROOT / "scripts/run_network.py", bundle / "scripts/run_network.py")
    for name in PUBLISHED_DOCS:
        target = bundle / "docs" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        copy2(ROOT / "docs" / name, target)
    (bundle / "НАЧАТЬ_ЗДЕСЬ.txt").write_text(START_HERE, encoding="utf-8-sig", newline="\r\n")


def build(output, python_archive):
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".college-windows-", dir=output.parent) as folder:
        workspace = Path(folder)
        if python_archive is None:
            name = f"python-{PYTHON_VERSION}-embed-amd64.zip"
            python_archive = workspace / name
            urlretrieve(f"https://www.python.org/ftp/python/{PYTHON_VERSION}/{name}", python_archive)
        bundle = workspace / BUNDLE
        bundle.mkdir()
        prepare_runtime(bundle, python_archive)
        prepare_project(bundle)
        staged = workspace / output.name
        scripts_dir = bundle / "runtime" / "Lib" / "site-packages"
        generated_commands = {scripts_dir / "bin", scripts_dir / "Scripts"}
        with ZipFile(staged, "w", ZIP_DEFLATED, compresslevel=4) as archive:
            for path in sorted(bundle.rglob("*")):
                if path.is_file() and generated_commands.isdisjoint(path.parents):
                    archive.write(path, path.relative_to(workspace))
        staged.replace(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "CollegeTeachers-Windows-x64.zip")
    parser.add_argument("--python-archive", type=Path, help="reuse the official Python embed ZIP")
    args = parser.parse_args()
    build(args.output.resolve(), args.python_archive)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
