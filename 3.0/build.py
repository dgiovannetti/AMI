"""
AMI 3.0 Build Script
Builds the AMI 3.0 application into a standalone executable using PyInstaller.
macOS: produces AMI.app (proper bundle + ad-hoc codesign) so Gatekeeper shows "AMI", not "Python".
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# First 4 bytes of Mach-O / fat binaries (either endian)
_MACHO_OR_FAT_MAGIC = frozenset(
    {
        0xFEEDFACE,
        0xFEEDFACF,
        0xCEFAEDFE,
        0xCFFAEDFE,
        0xCAFEBABE,
        0xCAFEBABF,
        0xBEBAFECA,
    }
)


def check_requirements() -> bool:
    print("Checking requirements...")
    required = [
        "PyQt6",
        "requests",
        "matplotlib",
        "numpy",
        "ping3",
        "psutil",
        "platformdirs",
        "jsonschema",
    ]
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_") if pkg == "jsonschema" else pkg)
            print(f"  [OK] {pkg}")
        except ImportError:
            print(f"  [FAIL] {pkg}")
            missing.append(pkg)
    if missing:
        print(f"\nMissing: {', '.join(missing)}. Install with: pip install -r requirements.txt")
        return False
    try:
        __import__("PyInstaller")
        print("  [OK] PyInstaller")
    except ImportError:
        print("  [FAIL] PyInstaller. Install with: pip install pyinstaller")
        return False
    return True


def _is_macho_file(path: Path) -> bool:
    try:
        if not path.is_file():
            return False
        if path.stat().st_size < 4:
            return False
        with open(path, "rb") as f:
            b = f.read(4)
        le = int.from_bytes(b, "little")
        be = int.from_bytes(b, "big")
        return le in _MACHO_OR_FAT_MAGIC or be in _MACHO_OR_FAT_MAGIC
    except OSError:
        return False


def _codesign_macos_app(app_path: Path) -> None:
    """
    Sign every Mach-O inside the bundle first, then the .app (recommended vs --deep alone).
    Ad-hoc (-) still triggers Gatekeeper on quarantined downloads; Developer ID + notarization is the full fix.
    """
    identity = os.environ.get("AMI_CODESIGN_IDENTITY", "-").strip() or "-"
    inner: list[Path] = []
    for p in app_path.rglob("*"):
        if p.is_file() and _is_macho_file(p):
            inner.append(p)
    inner.sort(key=lambda p: len(p.parts), reverse=True)
    ts_none = identity == "-"
    for p in inner:
        cmd = ["codesign", "--force", "--sign", identity, str(p)]
        if ts_none:
            cmd.append("--timestamp=none")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[codesign inner warn] {p}: {r.stderr.strip() or r.stdout.strip()}")
    cmd = ["codesign", "--force", "--sign", identity, str(app_path)]
    if ts_none:
        cmd.append("--timestamp=none")
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=str(app_path.parent))


def _write_macos_qt_conf(app_path: Path) -> None:
    """
    Qt 6 on macOS resolves install paths via CFBundle; PyInstaller's layout breaks that on
    newer macOS (crash in CFBundleCopyBundleURL). qt.conf next to the executable forces
    filesystem paths — see https://doc.qt.io/qt-6/qt-conf.html
    """
    contents = app_path / "Contents"
    resources = contents / "Resources"
    qt6 = contents / "Frameworks" / "PyQt6" / "Qt6"
    if not qt6.is_dir():
        print(f"[WARN] Skip qt.conf: missing {qt6}")
        return
    resources.mkdir(parents=True, exist_ok=True)
    # In Resources: evita che codesign tratti MacOS/qt.conf come “subcomponent” non firmato.
    conf = resources / "qt.conf"
    conf.write_text(
        "[Paths]\n"
        "Prefix = ../Frameworks/PyQt6/Qt6\n"
        "Plugins = plugins\n"
        "Libraries = lib\n",
        encoding="utf-8",
    )
    print(f"[OK] Wrote {conf}")


def build_executable() -> bool:
    print("\nBuilding executable...")
    root_dir = Path(__file__).parent
    src_dir = root_dir / "src"
    resources_dir = root_dir / "resources"
    config_file = root_dir / "config.json"
    schema_file = root_dir / "config.schema.json"
    main_script = src_dir / "ami" / "main.py"
    icon_file = resources_dir / "ami.ico" if (resources_dir / "ami.ico").exists() else None
    dist_dir = root_dir / "dist"

    if sys.platform == "darwin":
        spec = root_dir / "ami_macos.spec"
        if not spec.exists():
            print(f"[FAIL] Missing {spec.name}")
            return False
        args = ["pyinstaller", "--noconfirm", str(spec)]
        print(f"Running: {' '.join(args)}")
        try:
            subprocess.run(args, check=True, cwd=str(root_dir))
        except subprocess.CalledProcessError as e:
            print(f"\n[FAIL] Build failed: {e}")
            return False
        app_path = dist_dir / "AMI.app"
        if not app_path.is_dir():
            print(f"\n[FAIL] Expected {app_path}")
            return False
        _write_macos_qt_conf(app_path)
        try:
            _codesign_macos_app(app_path)
            print("[OK] macOS codesign completed")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"[WARN] codesign skipped or failed: {e}")
        print("\n[OK] Build successful!")
        print(f"Output: {app_path}")
        return True

    args = [
        "pyinstaller",
        "--name=AMI",
        "--windowed",
        "--onedir",
        "--noconsole" if sys.platform == "win32" else "",
        f"--icon={icon_file}" if icon_file else "",
        f"--add-data={config_file}{os.pathsep}.",
        f"--add-data={schema_file}{os.pathsep}." if schema_file.exists() else "",
        f"--add-data={resources_dir}{os.pathsep}resources",
        f"--paths={src_dir}",
        "--hidden-import=ami",
        "--hidden-import=ami.core",
        "--hidden-import=ami.core.config",
        "--hidden-import=ami.core.models",
        "--hidden-import=ami.core.paths",
        "--hidden-import=ami.services",
        "--hidden-import=ami.services.network_monitor",
        "--hidden-import=ami.services.logger",
        "--hidden-import=ami.services.notifier",
        "--hidden-import=ami.services.api_server",
        "--hidden-import=ami.services.updater",
        "--hidden-import=ami.services.speed_test",
        "--hidden-import=ami.ui",
        "--hidden-import=ami.ui.tray_app",
        "--hidden-import=ami.ui.dashboard",
        "--hidden-import=ami.ui.splash_screen",
        "--hidden-import=ami.ui.settings_dialog",
        "--hidden-import=ami.ui.update_dialog",
        "--hidden-import=ami.ui.compact_status",
        "--hidden-import=ami.ui.themes",
        "--hidden-import=ping3",
        "--hidden-import=matplotlib",
        "--hidden-import=numpy",
        "--collect-all=matplotlib",
        "--noconfirm",
        str(main_script),
    ]
    args = [a for a in args if a]
    print(f"Running: {' '.join(args)}")
    try:
        subprocess.run(args, check=True, cwd=str(root_dir))
        print("\n[OK] Build successful!")
        exe_path = dist_dir / "AMI.exe" if sys.platform == "win32" else dist_dir / "AMI"
        if exe_path.exists() or (sys.platform == "darwin" and (dist_dir / "AMI").is_dir()):
            print(f"Output: {dist_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[FAIL] Build failed: {e}")
        return False


def create_package() -> None:
    print("\nCreating package...")
    root = Path(__file__).parent
    dist_dir = root / "dist"
    package_dir = dist_dir / "AMI-Package"
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)

    if sys.platform == "darwin":
        app_src = dist_dir / "AMI.app"
        if not app_src.is_dir():
            raise FileNotFoundError(f"AMI.app not found under {dist_dir}; build on macOS first.")
        shutil.copytree(app_src, package_dir / "AMI.app")
    else:
        exe_src = dist_dir / "AMI"
        if exe_src.is_dir():
            for f in exe_src.iterdir():
                dst = package_dir / f.name
                if f.is_file():
                    shutil.copy2(f, dst)
                else:
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(f, dst)
        else:
            shutil.copy2(exe_src, package_dir / ("AMI.exe" if sys.platform == "win32" else "AMI"))
    for name in ["config.json", "config.schema.json"]:
        src = root / name
        if src.exists():
            shutil.copy2(src, package_dir / name)
    if (root / "resources").exists():
        rsrc = package_dir / "resources"
        if rsrc.exists():
            shutil.rmtree(rsrc)
        shutil.copytree(root / "resources", rsrc)
    if sys.platform == "darwin":
        readme = package_dir / "LEGGIMI_macOS.txt"
        readme.write_text(
            """AMI su macOS — leggi prima di aprire
=====================================

Dopo aver estratto lo ZIP dalla pagina Release, nella STESSA cartella dovresti vedere:
  • AMI.app  (icona applicazione — usa SOLO questa)
  • questo file LEGGIMI_macOS.txt
  • config.json, cartella resources, ecc.

Icona nella barra dei menu in alto: forma scura (● / anello / ✕) che si adatta al tema; se non la vedi, controlla «>>» a destra nella menu bar.
C’è anche l’icona AMI nel Dock: clic per riaprire menu / dashboard se hai chiuso le finestre.
Click sinistro sull’icona in menu bar apre il menu; doppio click apre la dashboard.
Il primo avvio dal .app è più lento che `python -m ami.main` (PyInstaller carica librerie).

1) Avvia SOLO l’applicazione «AMI» (icona AMI.app).
   Puoi trascinare AMI.app in Applicazioni e aprirla da lì.

2) NON aprire il file «AMI» nudo dentro il pacchetto:
   tasto destro su AMI.app → «Mostra contenuto pacchetto» → Contents → MacOS → AMI
   Quello è solo il motore interno: macOS può mostrarlo come «Python» o dare errori.
   Non è un bug di AMI: Finder non deve usare quel file direttamente.

3) Download da browser (quarantena):
   Apri Terminale, vai nella cartella AMI-Package (dove c’è AMI.app) e esegui:

   xattr -cr AMI.app
   open AMI.app

4) Se Apple blocca ancora l’apertura:
   Impostazioni → Privacy e sicurezza → scorri fino al messaggio su AMI → «Apri comunque».
   Senza account Apple Developer (firma + notarizzazione) l’avviso può comparire al primo avvio.

ZIP corretto dalla pagina Release: nome file deve contenere «macos», es. AMI-v3.1.4-macos.zip
(non usare vecchi pacchetti «AMI-macOS.zip» se ancora presenti).
""",
            encoding="utf-8",
        )
    print(f"[OK] Package: {package_dir}")


def main() -> int:
    print("=" * 60)
    print("AMI 3.0 Build")
    print("=" * 60)
    if not check_requirements():
        return 1
    if not build_executable():
        return 1
    try:
        create_package()
    except FileNotFoundError as e:
        print(f"\n[FAIL] {e}")
        return 1
    print("\n[OK] Build completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
