"""
Telegram Username Hunter PRO
PyInstaller Windows Build Script
Builds both Portable (OneFile) and Installer (Inno Setup) packages.
"""
import subprocess
import sys
import os
from pathlib import Path


def build():
    root = Path(__file__).parent.resolve()
    print("=== Starting Build for Telegram Username Hunter PRO ===")

    icon_path = root / "assets" / "icon.ico"
    icon_arg = [f"--icon={icon_path}"] if icon_path.exists() else []

    # 1. Build Onedir for Installer
    print("\n--- 1. Building Directory (Onedir) for Installer ---")
    cmd_onedir = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=TelegramUsernameHunterPRO",
        "--collect-all=customtkinter",
        "--add-data=telegram_username_hunter;telegram_username_hunter",
        *icon_arg,
        str(root / "main.py")
    ]
    res_onedir = subprocess.run(cmd_onedir, cwd=str(root))
    if res_onedir.returncode != 0:
        print(f"[ERROR] Onedir build failed with code {res_onedir.returncode}")
        sys.exit(res_onedir.returncode)

    # 2. Build Onefile Portable
    print("\n--- 2. Building Portable Standalone (OneFile) ---")
    cmd_onefile = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=TelegramUsernameHunter_Portable",
        "--collect-all=customtkinter",
        "--add-data=telegram_username_hunter;telegram_username_hunter",
        *icon_arg,
        str(root / "main.py")
    ]
    res_onefile = subprocess.run(cmd_onefile, cwd=str(root))
    if res_onefile.returncode != 0:
        print(f"[ERROR] Onefile build failed with code {res_onefile.returncode}")
        sys.exit(res_onefile.returncode)

    # 3. Compile Inno Setup Installer if ISCC is available
    iscc_candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe")
    ]
    iscc_path = None
    for p in iscc_candidates:
        if p.exists():
            iscc_path = p
            break

    iss_file = root / "packaging" / "windows" / "setup.iss"
    if iscc_path and iss_file.exists():
        print(f"\n--- 3. Compiling Inno Setup Installer using {iscc_path} ---")
        cmd_iscc = [str(iscc_path), str(iss_file)]
        res_iscc = subprocess.run(cmd_iscc, cwd=str(root))
        if res_iscc.returncode == 0:
            print("[SUCCESS] Inno Setup Installer created successfully!")
        else:
            print(f"[WARNING] Inno Setup compilation returned {res_iscc.returncode}")
    else:
        print("\n[NOTE] ISCC compiler not found. Skipping Inno Setup packaging.")

    dist = root / "dist"
    print("\n================== BUILD FINISHED ==================")
    print(f"Artifacts directory: {dist}")
    for item in dist.glob("*.exe"):
        size_mb = item.stat().st_size / (1024 * 1024)
        print(f" - {item.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    build()
