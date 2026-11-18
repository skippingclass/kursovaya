"""Русские подписи стандартных диалогов и команд Qt."""
from PyQt6.QtCore import QLibraryInfo, QLocale, QTranslator


def install_russian_translations(app):
    QLocale.setDefault(QLocale("ru_RU"))
    translator = QTranslator(app)
    directory = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load("qtbase_ru", directory):
        app.installTranslator(translator)
        app._qt_translator = translator
