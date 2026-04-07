import subprocess
import sys
from pathlib import Path
from tkinter import Tk, messagebox

BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHONW_PATH = BASE_DIR / ".venv" / "Scripts" / "pythonw.exe"
MAIN_PATH = BASE_DIR / "main.py"


def show_error(message: str) -> None:
    """Display a friendly startup error without opening a full console window."""
    root = Tk()
    root.withdraw()
    messagebox.showerror("Wanptek PSU Controller", message)
    root.destroy()


def main() -> None:
    """Launch the GUI application with the project virtual environment."""
    if not VENV_PYTHONW_PATH.exists():
        show_error(
            "Virtual environment not found.\n\n"
            "Create it with Python 3.10, install the dependencies, then try again."
        )
        return

    try:
        subprocess.Popen([str(VENV_PYTHONW_PATH), str(MAIN_PATH)], cwd=BASE_DIR)
    except OSError as exc:
        show_error(f"Unable to start the application.\n\n{exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
