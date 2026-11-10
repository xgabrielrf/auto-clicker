"""Gera o executável (Windows) com PyInstaller.

Uso (na raiz do projeto):
    pip install -r requirements-dev.txt
    python tools/build.py

Saída: dist/Auto-Clicker-v<versão>.exe  (a versão vem de config.APP_VERSION).
"""
from __future__ import annotations

import base64
import io
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config                                   # noqa: E402
from assets.icon_data import ICON_B64            # noqa: E402

NAME = f"Auto-Clicker-v{config.APP_VERSION}"

VERSION_INFO = """\
VSVersionInfo(
  ffi=FixedFileInfo(filevers=({a}, {b}, {c}, 0), prodvers=({a}, {b}, {c}, 0), mask=0x3f, flags=0x0,
                    OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', ''),
      StringStruct('FileDescription', '{name}'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('InternalName', '{name}'),
      StringStruct('OriginalFilename', '{exe}'),
      StringStruct('ProductName', '{name}'),
      StringStruct('ProductVersion', '{version}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def make_ico(path: Path) -> None:
    """Converte o PNG embutido (base64) em .ico para o ícone do arquivo .exe."""
    from PIL import Image

    img = Image.open(io.BytesIO(base64.b64decode(ICON_B64))).convert("RGBA")
    img.save(path, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128)])


def main() -> None:
    a, b, c = (int(part) for part in config.APP_VERSION.split("."))
    work = Path(tempfile.mkdtemp(prefix="ac-build-"))
    try:
        icon = work / "icon.ico"
        make_ico(icon)
        version_file = work / "version_info.txt"
        version_file.write_text(
            VERSION_INFO.format(a=a, b=b, c=c, name=config.APP_NAME,
                                version=config.APP_VERSION, exe=f"{NAME}.exe"),
            encoding="utf-8")

        cmd = [
            sys.executable, "-m", "PyInstaller", "main.py",
            "--noconfirm", "--clean", "--onefile", "--windowed",
            "--name", NAME,
            "--icon", str(icon),
            "--version-file", str(version_file),
            "--collect-data", "customtkinter",
            "--distpath", str(ROOT / "dist"),
            "--workpath", str(work / "build"),
            "--specpath", str(work),
        ]
        subprocess.run(cmd, cwd=ROOT, check=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print(f"\nExecutável gerado: {ROOT / 'dist' / (NAME + '.exe')}")


if __name__ == "__main__":
    main()
