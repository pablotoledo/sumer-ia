#!/usr/bin/env python3
"""
Build script for Video Frame Capture application.
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


def run_command(command, cwd=None, check=True):
    """Run a command and return the result"""
    print(f"Running: {command}")
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result


def clean_build_artifacts(project_root):
    """Clean previous build artifacts"""
    print("Cleaning build artifacts...")

    artifacts = [
        "build",
        "dist",
        "*.egg-info",
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".coverage",
        ".pytest_cache"
    ]

    for artifact in artifacts:
        for path in project_root.glob(f"**/{artifact}"):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                print(f"Removed directory: {path}")
            elif path.is_file():
                path.unlink()
                print(f"Removed file: {path}")


def install_dependencies(project_root):
    """Install project dependencies"""
    print("Installing dependencies...")

    # Try Poetry first
    if shutil.which("poetry"):
        run_command("poetry install", cwd=project_root)
    else:
        # Fall back to pip
        run_command("pip install -r requirements.txt", cwd=project_root)


def run_tests(project_root):
    """Run the test suite"""
    print("Running tests...")

    if shutil.which("poetry"):
        result = run_command("poetry run pytest", cwd=project_root, check=False)
    else:
        result = run_command("python -m pytest", cwd=project_root, check=False)

    return result.returncode == 0


def check_code_quality(project_root):
    """Run code quality checks"""
    print("Checking code quality...")

    checks_passed = True

    # Black formatting check
    if shutil.which("poetry"):
        result = run_command("poetry run black --check src/", cwd=project_root, check=False)
    else:
        result = run_command("black --check src/", cwd=project_root, check=False)

    if result.returncode != 0:
        print("Code formatting issues found. Run 'black src/' to fix.")
        checks_passed = False

    # Flake8 linting
    if shutil.which("poetry"):
        result = run_command("poetry run flake8 src/", cwd=project_root, check=False)
    else:
        result = run_command("flake8 src/", cwd=project_root, check=False)

    if result.returncode != 0:
        print("Linting issues found.")
        checks_passed = False

    return checks_passed


def build_with_pyinstaller(project_root, output_dir):
    """Build standalone executable with PyInstaller"""
    print("Building with PyInstaller...")

    output_dir.mkdir(parents=True, exist_ok=True)

    main_script = project_root / "src" / "video_frame_capture" / "main.py"

    pyinstaller_args = [
        "--name=VideoFrameCapture",
        "--windowed",
        "--onefile",
        f"--distpath={output_dir}",
        f"--workpath={output_dir / 'build'}",
        f"--specpath={output_dir}",
        "--add-data=src/video_frame_capture/resources;resources",
        "--hidden-import=cv2",
        "--hidden-import=numpy",
        "--hidden-import=PIL",
        str(main_script)
    ]

    # Platform-specific options
    if sys.platform == "win32":
        pyinstaller_args.extend([
            "--icon=src/video_frame_capture/resources/icons/app_icon.ico"
        ])
    elif sys.platform == "darwin":
        pyinstaller_args.extend([
            "--icon=src/video_frame_capture/resources/icons/app_icon.icns"
        ])

    command = f"pyinstaller {' '.join(pyinstaller_args)}"

    if shutil.which("poetry"):
        command = f"poetry run {command}"

    run_command(command, cwd=project_root)

    print(f"Executable built: {output_dir / 'VideoFrameCapture'}")


def build_with_briefcase(project_root):
    """Build with Briefcase"""
    print("Building with Briefcase...")

    if shutil.which("poetry"):
        run_command("poetry run briefcase create", cwd=project_root)
        run_command("poetry run briefcase build", cwd=project_root)
        run_command("poetry run briefcase package", cwd=project_root)
    else:
        run_command("briefcase create", cwd=project_root)
        run_command("briefcase build", cwd=project_root)
        run_command("briefcase package", cwd=project_root)


def create_installer(project_root, output_dir):
    """Create platform-specific installer"""
    print("Creating installer...")

    if sys.platform == "win32":
        create_windows_installer(project_root, output_dir)
    elif sys.platform == "darwin":
        create_macos_installer(project_root, output_dir)
    elif sys.platform.startswith("linux"):
        create_linux_installer(project_root, output_dir)


def create_windows_installer(project_root, output_dir):
    """Create Windows installer using NSIS or similar"""
    # This would use NSIS or WiX to create MSI installer
    print("Windows installer creation not implemented yet")


def create_macos_installer(project_root, output_dir):
    """Create macOS installer"""
    # This would create DMG or PKG installer
    print("macOS installer creation not implemented yet")


def create_linux_installer(project_root, output_dir):
    """Create Linux installer"""
    # This would create DEB, RPM, or AppImage
    print("Linux installer creation not implemented yet")


def main():
    """Main build script"""
    parser = argparse.ArgumentParser(description="Build Video Frame Capture application")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--test", action="store_true", help="Run tests")
    parser.add_argument("--check", action="store_true", help="Run code quality checks")
    parser.add_argument("--build", choices=["pyinstaller", "briefcase"], help="Build method")
    parser.add_argument("--installer", action="store_true", help="Create installer")
    parser.add_argument("--output", type=str, default="dist", help="Output directory")
    parser.add_argument("--all", action="store_true", help="Run all steps")

    args = parser.parse_args()

    # Get project root
    project_root = Path(__file__).parent.parent
    output_dir = project_root / args.output

    try:
        # Clean if requested
        if args.clean or args.all:
            clean_build_artifacts(project_root)

        # Install dependencies
        if args.build or args.all:
            install_dependencies(project_root)

        # Run tests if requested
        if args.test or args.all:
            if not run_tests(project_root):
                print("Tests failed!")
                return 1

        # Check code quality if requested
        if args.check or args.all:
            if not check_code_quality(project_root):
                print("Code quality checks failed!")
                return 1

        # Build if requested
        if args.build == "pyinstaller" or args.all:
            build_with_pyinstaller(project_root, output_dir)
        elif args.build == "briefcase":
            build_with_briefcase(project_root)

        # Create installer if requested
        if args.installer or args.all:
            create_installer(project_root, output_dir)

        print("Build completed successfully!")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())