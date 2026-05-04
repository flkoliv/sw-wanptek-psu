import ctypes
import logging
import os
import tkinter
from pathlib import Path
from logging.handlers import RotatingFileHandler

import customtkinter
from customtkinter.windows.widgets.appearance_mode.appearance_mode_tracker import (
    AppearanceModeTracker,
)
from customtkinter.windows.widgets.scaling.scaling_tracker import ScalingTracker

from wanptek_controller import PSUController, PSUModel, PSUView

_PACKAGE_DIR = Path(__file__).parent

APP_ID = "monentreprise.psu_controller.1.0"
APP_VERSION = "1.0"
WINDOW_TITLE = f"PSU controller {APP_VERSION}"
WINDOW_SIZE = "280x310"
BG_COLOR = "#23272d"
FAVICON_PATH = _PACKAGE_DIR / "images" / "favicon.png"
ICON_PATH = _PACKAGE_DIR / "images" / "wanptek.ico"

LOG_FORMAT = "%(asctime)s %(message)s"
LOG_DIR = Path.home() / ".wanptek_controller" / "logs"
LOG_FILE = LOG_DIR / "app.log"
LOG_MAX_BYTES = 1_000_000
LOG_BACKUP_COUNT = 5
APP_LOGGERS = {
    "__main__",
    "PSUModel", "PSUController", "PSUView",
    "wanptek_controller.PSUModel",
    "wanptek_controller.PSUController",
    "wanptek_controller.PSUView",
    "wanptek_controller.main",
}


if os.name == "nt":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)


class App(customtkinter.CTk):
    """Main application window that wires together model, view and controller."""

    def __init__(self) -> None:
        """Create the main window and initialize the MVC components."""
        super().__init__()
        self._closing = False

        self.wm_attributes("-class", "WanptekController")
        self.title(WINDOW_TITLE)
        self.configure(fg_color=BG_COLOR)
        self.geometry(WINDOW_SIZE)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        self._center_window()

        self.model = PSUModel.PSUModel()
        self.view = PSUView.PsuWindow(self)
        self.view.grid(row=0, column=0, padx=0, pady=0)

        self.controller = PSUController.PSUController(self.model, self.view)
        self.view.set_controller(self.controller)
        self.controller.start()

        self._set_window_icons()

    def _set_window_icons(self) -> None:
        """Load and apply the application icons for the main window."""
        icon_image = tkinter.PhotoImage(file=str(FAVICON_PATH))
        self.iconphoto(True, icon_image)
        self._icon_image = icon_image
        if os.name == "nt":
            self.iconbitmap(str(ICON_PATH))

    def _center_window(self) -> None:
        """Center the main window on the current screen."""
        self.update_idletasks()
        width, height = (int(value) for value in WINDOW_SIZE.split("x"))
        x_pos = (self.winfo_screenwidth() - width) // 2
        y_pos = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x_pos}+{y_pos}")

    def close_window(self) -> None:
        """Close secondary windows first, then destroy the main application."""
        if self._closing:
            return

        self._closing = True
        print("Closing Wanptek PSU Controller...")
        logging.getLogger(__name__).info("Application shutdown requested")
        self.view.begin_shutdown()
        self.controller.stop()
        self._cleanup_customtkinter_trackers()
        self.destroy()

    def _cleanup_customtkinter_trackers(self) -> None:
        """Remove this window from CustomTkinter background trackers."""
        try:
            if self in AppearanceModeTracker.app_list:
                AppearanceModeTracker.app_list.remove(self)
            if not AppearanceModeTracker.app_list:
                AppearanceModeTracker.update_loop_running = False
        except Exception:
            pass

        try:
            ScalingTracker.window_widgets_dict.pop(self, None)
            ScalingTracker.window_dpi_scaling_dict.pop(self, None)
            if not ScalingTracker.window_widgets_dict:
                ScalingTracker.update_loop_running = False
        except Exception:
            pass


def configure_logging() -> None:
    """Configure rotating file logging and silence normal console output."""
    class AppLogFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if record.name in APP_LOGGERS:
                return record.levelno >= logging.INFO
            return record.levelno >= logging.ERROR

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    file_handler.addFilter(AppLogFilter())

    root_logger.addHandler(file_handler)

    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("pygame").setLevel(logging.WARNING)
    logging.getLogger("pymodbus").setLevel(logging.ERROR)


def main() -> None:
    """Run the desktop application."""
    configure_logging()
    print("Starting Wanptek PSU Controller...")
    logging.getLogger(__name__).info("Application started")
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
