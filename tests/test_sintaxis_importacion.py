"""Pruebas de sintaxis e importación."""
import importlib
import pathlib
import py_compile

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY_FILES = sorted([ROOT / "main.py", *(ROOT / "src").glob("*.py"),
                   *(ROOT / "tests").glob("*.py")])


@pytest.mark.parametrize("path", PY_FILES, ids=lambda p: p.name)
def test_sintaxis(path):
    py_compile.compile(str(path), doraise=True)


@pytest.mark.parametrize("module", ["src.settings", "src.entities", "src.effects", "src.game"])
def test_importacion_logica(module):
    """Los módulos de lógica se importan sin necesitar Pygame."""
    importlib.import_module(module)


def test_sin_rutas_absolutas_del_entorno():
    """Ningún archivo del proyecto contiene rutas de la máquina de desarrollo."""
    forbidden = ("/home/", "C:\\Users", "/mnt/", "/tmp/claude")
    for path in PY_FILES:
        if path.name == pathlib.Path(__file__).name:
            continue  # este archivo contiene las cadenas a buscar
        text = path.read_text(encoding="utf-8")
        for f in forbidden:
            assert f not in text, f"{path.name} contiene la ruta {f}"


def test_requirements_declara_pygame():
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "pygame" in req
