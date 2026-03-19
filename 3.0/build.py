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


def _codesign_macos_app(app_path: Path) -> None:
    """Ad-hoc (-) or Developer ID if AMI_CODESIGN_IDENTITY is set."""
    identity = os.environ.get("AMI_CODESIGN_IDENTITY", "-").strip() or "-"
    cmd = [
        "codesign",
        "--force",
        "--deep",
        "--sign",
        identity,
        str(app_path),
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=str(app_path.parent))


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
