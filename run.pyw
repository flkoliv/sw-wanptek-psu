import subprocess
import sys
from pathlib import Path
from tkinter import Tk, messagebox

BASE_DIR = Path(__file__).resolve().parent
MAIN_PATH = BASE_DIR / "main.py"

if sys.platform == "win32":
    VENV_PYTHON_PATH = BASE_DIR / ".venv" / "Scripts" / "pythonw.exe"
else:
    VENV_PYTHON_PATH = BASE_DIR / ".venv" / "bin" / "python3"


def show_error(message: str) -> None:
    """Display a friendly startup error without opening a full console window."""
    root = Tk()
    root.withdraw()
    messagebox.showerror("Wanptek PSU Controller", message)
    root.destroy()


def main() -> None:
    """Launch the GUI application with the project virtual environment."""
    if not VENV_PYTHON_PATH.exists():
        show_error(
            "Virtual environment not found.\n\n"
            "Create it with Python 3.10, install the dependencies, then try again."
        )
        return

    try:
        subprocess.Popen([str(VENV_PYTHON_PATH), str(MAIN_PATH)], cwd=BASE_DIR)
    except OSError as exc:
        show_error(f"Unable to start the application.\n\n{exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
