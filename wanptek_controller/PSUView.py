import logging
import os
import threading
import time
import tkinter
import tkinter.messagebox as messagebox
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import customtkinter
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import serial.tools.list_ports
from matplotlib.animation import FuncAnimation
from PIL import Image
from tkdial import Dial

try:
    import pygame
    _PYGAME_AVAILABLE = True
except ImportError:
    _PYGAME_AVAILABLE = False

BACKGROUND_COLOR = "#23272d"
MUTED_TEXT_COLOR = "#737574"
BUTTON_TEXT_COLOR = "grey40"
BUTTON_BG_COLOR = "grey10"
BUTTON_HOVER_COLOR = "grey25"

_PACKAGE_DIR = Path(__file__).parent
LOGO_PATH = _PACKAGE_DIR / "images" / "logo.png"
GRAPH_ICON_PATH = _PACKAGE_DIR / "images" / "favicon.png"
SOUND_PATH = _PACKAGE_DIR / "ressources" / "censor-beep.wav"
DIGITAL_FONT_PATH = _PACKAGE_DIR / "ressources" / "digital-7.ttf"
SONO_FONT_PATH = _PACKAGE_DIR / "ressources" / "Sono-Regular.ttf"
GRAPH_REFRESH_MS = 500

log = logging.getLogger(__name__)


class LCDFrame(customtkinter.CTkFrame):
    """Display the PSU measurements and status labels in an LCD-like layout."""

    def __init__(self, parent) -> None:
        """Create the fixed labels and values shown on the main display."""
        super().__init__(parent)
        self.configure(fg_color="black")

        customtkinter.FontManager.load_font(str(DIGITAL_FONT_PATH))
        customtkinter.FontManager.load_font(str(SONO_FONT_PATH))

        logo_image = customtkinter.CTkImage(
            light_image=Image.open(LOGO_PATH),
            size=(100, 13),
        )
        self.logo_label = customtkinter.CTkLabel(self, text="", image=logo_image, height=13)
        self.logo_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="sw")

        self.slogan_label = customtkinter.CTkLabel(
            self,
            text="DC power supply",
            text_color=MUTED_TEXT_COLOR,
            font=("Sono-Regular", 10),
            height=10,
        )
        self.slogan_label.grid(row=1, column=0, padx=10, pady=0, sticky="nw")

        self.voltage_label = customtkinter.CTkLabel(
            self,
            text="00",
            font=("digital-7", 40),
            text_color="white",
            height=5,
        )
        self.voltage_label.grid(row=2, column=0, padx=10, pady=(10, 0), sticky="e")
        self.v_label = customtkinter.CTkLabel(
            self,
            text="V",
            font=("Sono-Regular", 20),
            text_color=MUTED_TEXT_COLOR,
        )
        self.v_label.grid(row=2, column=1, padx=10, pady=(10, 0))

        self.cv_label = customtkinter.CTkLabel(
            self,
            text="C. V",
            font=("Sono-Regular", 8),
            text_color="black",
            height=2,
        )
        self.cv_label.grid(row=3, column=1, padx=0, pady=0)

        self.current_label = customtkinter.CTkLabel(
            self,
            text="00",
            font=("digital-7", 40),
            text_color="white",
        )
        self.current_label.grid(row=4, column=0, padx=10, pady=0, sticky="e")
        self.a_label = customtkinter.CTkLabel(
            self,
            text=" A",
            font=("Sono-Regular", 20),
            text_color=MUTED_TEXT_COLOR,
        )
        self.a_label.grid(row=4, column=1, padx=10, pady=(5, 5))

        self.cc_label = customtkinter.CTkLabel(
            self,
            text="C. C",
            font=("Sono-Regular", 8),
            text_color="black",
            height=2,
        )
        self.cc_label.grid(row=5, column=1, padx=0, pady=0)

        self.power_label = customtkinter.CTkLabel(
            self,
            text=" OFF",
            font=("digital-7", 40),
            text_color="white",
        )
        self.power_label.grid(row=6, column=0, padx=10, pady=0, sticky="e")
        self.w_label = customtkinter.CTkLabel(
            self,
            text=" W",
            font=("Sono-Regular", 20),
            text_color=MUTED_TEXT_COLOR,
        )
        self.w_label.grid(row=6, column=1, padx=10, pady=(5, 5))

        self.ocp_label = customtkinter.CTkLabel(
            self,
            text="OCP",
            font=("Sono-Regular", 8),
            text_color="black",
            height=2,
        )
        self.ocp_label.grid(row=7, column=0, padx=0, pady=(10, 0), sticky="e")
        self.out_label = customtkinter.CTkLabel(
            self,
            text="OUT",
            font=("Sono-Regular", 8),
            text_color="black",
            height=2,
        )
        self.out_label.grid(row=7, column=1, padx=(10, 0), pady=(10, 0), sticky="w")

        self._logo_image = logo_image


class KnobFrame(customtkinter.CTkFrame):
    """Display the two adjustment knobs and the connection status LED."""

    def __init__(self, parent) -> None:
        """Create the voltage/current knobs and the communication indicator."""
        super().__init__(parent)
        self.configure(fg_color=BACKGROUND_COLOR)

        self.voltage_knob = self._create_knob("V ")
        self.voltage_knob.grid(row=0, column=0, padx=0, pady=10, columnspan=2)

        self.current_knob = self._create_knob("A ")
        self.current_knob.grid(row=1, column=0, padx=0, pady=10, columnspan=2)

        self.led_rx = customtkinter.CTkCanvas(
            self,
            width=16,
            height=16,
            bg=BACKGROUND_COLOR,
            highlightthickness=0,
            bd=0,
        )
        self.led_rx_circle = self.led_rx.create_aa_circle(8, 8, radius=5, fill="grey20")
        self.led_rx.grid(row=2, column=0, padx=0, pady=0, sticky="e")

        self.rx_label = customtkinter.CTkLabel(
            self,
            text="State",
            font=("Sono-Regular", 10),
            text_color=MUTED_TEXT_COLOR,
            height=5,
            width=80,
            anchor="w",
        )
        self.rx_label.grid(row=2, column=1, padx=10, pady=0, sticky="w")

    def _create_knob(self, text: str) -> Dial:
        """Return a knob widget configured with the application's visual style."""
        return Dial(
            self,
            bg=BACKGROUND_COLOR,
            start=0,
            end=0,
            color_gradient=("grey", "white"),
            scroll_steps=0.01,
            text_color="white",
            text=text,
            unit_width=3,
            unit_length=5,
            radius=25,
        )


class ButtonsFrame(customtkinter.CTkFrame):
    """Display the action buttons used to control the PSU and open dialogs."""

    def __init__(self, parent) -> None:
        """Create the bottom action bar of the main window."""
        super().__init__(parent)
        self.parent = parent
        self.configure(fg_color=BACKGROUND_COLOR)

        self.button_menu = self._create_button("Menu", self.open_setup_window)
        self.button_menu.grid(row=0, column=0, padx=2, pady=10)

        self.button_graph = self._create_button("Graph", self.open_graph_window)
        self.button_graph.grid(row=0, column=1, padx=2, pady=10)

        self.button_lock = self._create_button("Lock", self.push_button_lock)
        self.button_lock.grid(row=0, column=2, padx=2, pady=10)

        self.button_ocp = self._create_button("OCP", self.push_button_ocp)
        self.button_ocp.grid(row=0, column=3, padx=2, pady=10)

        self.button_out = self._create_button("OUT", self.push_button_out)
        self.button_out.grid(row=0, column=4, padx=2, pady=10)

    def _create_button(self, text: str, command) -> customtkinter.CTkButton:
        """Return a button configured with the shared application styling."""
        return customtkinter.CTkButton(
            self,
            text=text,
            text_color=BUTTON_TEXT_COLOR,
            command=command,
            width=25,
            fg_color=BUTTON_BG_COLOR,
            hover_color=BUTTON_HOVER_COLOR,
        )

    def open_setup_window(self) -> None:
        """Open the communication settings dialog."""
        self.setup_window = ToplevelWindow(self.parent.controller)

    def open_graph_window(self) -> None:
        """Open the live graph window."""
        self.parent.open_graph_window()

    def push_button_lock(self) -> None:
        """Queue a lock button action for the controller loop."""
        self.parent.controller.lock_button_pushed = True

    def push_button_ocp(self) -> None:
        """Queue an OCP button action for the controller loop."""
        self.parent.controller.ocp_button_pushed = True

    def push_button_out(self) -> None:
        """Queue an output button action for the controller loop."""
        self.parent.controller.out_button_pushed = True


class PsuWindow(customtkinter.CTkFrame):
    """Assemble the main PSU view and manage its dynamic visual state."""

    def __init__(self, parent) -> None:
        """Create the main interface blocks and initialize shared resources."""
        super().__init__(parent)
        self.controller = None
        self.connected = False
        self.killed = False
        self.sound = None
        self.sound_enabled = False
        self._blink_state = False
        self._last_alarm_toggle = 0.0
        self._graph_animation = None
        self._graph_figure = None
        self._controls_enabled = None
        self._lock_button_active = None
        self._ocp_button_active = None
        self._out_button_active = None
        self._shutting_down = False

        self.configure(fg_color=BACKGROUND_COLOR)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        top_frame = customtkinter.CTkFrame(self, fg_color=BACKGROUND_COLOR)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.lcd_frame = LCDFrame(top_frame)
        self.lcd_frame.grid(row=0, column=0, padx=5, pady=(10, 0), sticky="nsw")

        self.knob_frame = KnobFrame(top_frame)
        self.knob_frame.grid(row=0, column=1, padx=5, pady=(10, 0), sticky="nsw")

        self.buttons_frame = ButtonsFrame(self)
        self.buttons_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=(10, 0))

        self._init_sound()
        self._init_legacy_aliases()

    def _init_sound(self) -> None:
        """Initialize the optional alarm sound without breaking the UI on failure."""
        if not _PYGAME_AVAILABLE:
            self.sound_enabled = False
            log.warning("Alarm sound unavailable (pygame not installed)")
            return
        try:
            pygame.mixer.init()
            self.sound = pygame.mixer.Sound(str(SOUND_PATH))
            self.sound_enabled = True
        except Exception:
            self.sound_enabled = False
            log.warning("Alarm sound unavailable")

    def _schedule_on_ui_thread(self, callback, *args, **kwargs) -> None:
        """Run UI updates on Tk's main thread."""
        if self._shutting_down:
            return

        try:
            if threading.current_thread() is threading.main_thread():
                callback(*args, **kwargs)
            elif self.winfo_exists():
                self.after(0, lambda: callback(*args, **kwargs))
        except tkinter.TclError:
            pass

    def begin_shutdown(self) -> None:
        """Prevent new UI updates from being scheduled during shutdown."""
        self._shutting_down = True
        self.close_graph_window()

    def schedule_display_update(self, *args) -> None:
        """Schedule a display refresh from a worker thread."""
        self._schedule_on_ui_thread(self.update_display, *args)

    def schedule_status_update(
        self,
        text: str,
        color: str,
        *,
        buttons_enabled: bool,
    ) -> None:
        """Schedule a status refresh from a worker thread."""
        self._schedule_on_ui_thread(
            self.show_connection_status,
            text,
            color,
            buttons_enabled=buttons_enabled,
        )

    def schedule_set_disabled(self) -> None:
        """Schedule the disconnected visual state from a worker thread."""
        self._schedule_on_ui_thread(self.set_disabled)

    def _init_legacy_aliases(self) -> None:
        """Expose legacy attribute names expected by older parts of the code."""
        self.LCD_frame = self.lcd_frame
        self.LCD_frame.logoLabel = self.lcd_frame.logo_label
        self.LCD_frame.sloganLabel = self.lcd_frame.slogan_label
        self.LCD_frame.voltageLabel = self.lcd_frame.voltage_label
        self.LCD_frame.vLabel = self.lcd_frame.v_label
        self.LCD_frame.cvLabel = self.lcd_frame.cv_label
        self.LCD_frame.currentLabel = self.lcd_frame.current_label
        self.LCD_frame.ALabel = self.lcd_frame.a_label
        self.LCD_frame.ccLabel = self.lcd_frame.cc_label
        self.LCD_frame.powerLabel = self.lcd_frame.power_label
        self.LCD_frame.WLabel = self.lcd_frame.w_label
        self.LCD_frame.OCPLabel = self.lcd_frame.ocp_label
        self.LCD_frame.OUTLabel = self.lcd_frame.out_label

        self.knob_frame.voltageKnob = self.knob_frame.voltage_knob
        self.knob_frame.currentKnob = self.knob_frame.current_knob
        self.knob_frame.ledRx = self.knob_frame.led_rx
        self.knob_frame.ledRxCircle = self.knob_frame.led_rx_circle
        self.knob_frame.RxLabel = self.knob_frame.rx_label

        self.buttons_frame.buttonMenu = self.buttons_frame.button_menu
        self.buttons_frame.buttonGraph = self.buttons_frame.button_graph
        self.buttons_frame.buttonLock = self.buttons_frame.button_lock
        self.buttons_frame.buttonOCP = self.buttons_frame.button_ocp
        self.buttons_frame.buttonOut = self.buttons_frame.button_out

    def set_controller(self, controller) -> None:
        """Attach the controller after both model and view have been created."""
        self.controller = controller

    def show_connection_status(
        self,
        text: str,
        color: str,
        *,
        buttons_enabled: bool,
    ) -> None:
        """Update the connection status label and interactive controls."""
        if self._shutting_down:
            return

        self.knob_frame.rx_label.configure(text=text)

        if self._controls_enabled == buttons_enabled:
            return

        state = "normal" if buttons_enabled else "disabled"
        self.buttons_frame.button_graph.configure(state=state)
        self.buttons_frame.button_lock.configure(state=state)
        self.buttons_frame.button_ocp.configure(state=state)
        self.buttons_frame.button_out.configure(state=state)
        self._controls_enabled = buttons_enabled

    def set_disabled(self) -> None:
        """Display the disconnected visual state."""
        if self._shutting_down:
            return

        for label in (
            self.lcd_frame.voltage_label,
            self.lcd_frame.current_label,
            self.lcd_frame.power_label,
        ):
            label.configure(text_color="black")

        self.knob_frame.led_rx.itemconfig(self.knob_frame.led_rx_circle, fill="red")

    def set_enabled(self) -> None:
        """Display the connected visual state."""
        if self._shutting_down:
            return

        for label in (
            self.lcd_frame.voltage_label,
            self.lcd_frame.current_label,
            self.lcd_frame.power_label,
        ):
            label.configure(text_color="white")

        led_color = "green" if self._blink_state else "gray20"
        self.knob_frame.led_rx.itemconfig(self.knob_frame.led_rx_circle, fill=led_color)

    def update_display(
        self,
        connected,
        out_on,
        ocp_on,
        keyboard_locked,
        constant_current,
        alarm,
        real_voltage,
        real_current,
        set_voltage,
        set_current,
        max_voltage,
        max_current,
    ) -> None:
        """Refresh the full UI from the latest model and connection state."""
        if self._shutting_down:
            return

        self.connected = connected
        self._blink_state = not self._blink_state

        if connected:
            self.set_enabled()
        else:
            self.set_disabled()

        self.knob_frame.voltage_knob.configure(end=max_voltage or 0)
        self.knob_frame.current_knob.configure(end=max_current or 0)
        self._update_knob_state(connected, keyboard_locked, set_voltage, set_current, max_voltage, max_current)

        if alarm and connected:
            self._display_alarm_state()
        else:
            self._display_normal_state(
                out_on,
                ocp_on,
                constant_current,
                real_voltage,
                real_current,
                set_voltage,
                set_current,
            )

    def _update_knob_state(
        self,
        connected,
        keyboard_locked,
        set_voltage,
        set_current,
        max_voltage=0,
        max_current=0,
    ) -> None:
        """Enable or disable the knobs depending on the current control mode."""
        if connected and keyboard_locked:
            self.knob_frame.voltage_knob.configure(state="normal")
            self.knob_frame.current_knob.configure(state="normal")
            if self._lock_button_active is not True:
                self.buttons_frame.button_lock.configure(text_color="white")
                self._lock_button_active = True
            return

        if max_voltage > 0:
            self.knob_frame.voltage_knob.set(set_voltage)
        if max_current > 0:
            self.knob_frame.current_knob.set(set_current)
        if self._lock_button_active is not False:
            self.buttons_frame.button_lock.configure(text_color=BUTTON_TEXT_COLOR)
            self._lock_button_active = False

    def _display_normal_state(
        self,
        out_on,
        ocp_on,
        constant_current,
        real_voltage,
        real_current,
        set_voltage,
        set_current,
    ) -> None:
        """Render the normal operating state when no alarm is active."""
        if self._ocp_button_active != ocp_on:
            self.buttons_frame.button_ocp.configure(
                text_color="white" if ocp_on else BUTTON_TEXT_COLOR
            )
            self._ocp_button_active = ocp_on
        self.lcd_frame.ocp_label.configure(text_color="red" if ocp_on else "black")

        if out_on:
            if self._out_button_active is not True:
                self.buttons_frame.button_out.configure(text_color="white")
                self._out_button_active = True
            self.lcd_frame.out_label.configure(text_color="green")
            self.lcd_frame.voltage_label.configure(text=f"{real_voltage:05.2f}")
            self.lcd_frame.current_label.configure(text=f"{real_current:05.3f}")
            self.lcd_frame.power_label.configure(text=f"{real_current * real_voltage:05.1f}")
            self.lcd_frame.cc_label.configure(text_color="red" if constant_current else "black")
            self.lcd_frame.cv_label.configure(
                text_color="black" if constant_current else "green"
            )
            return

        if self._out_button_active is not False:
            self.buttons_frame.button_out.configure(text_color=BUTTON_TEXT_COLOR)
            self._out_button_active = False
        self.lcd_frame.cc_label.configure(text_color="black")
        self.lcd_frame.cv_label.configure(text_color="black")
        self.lcd_frame.out_label.configure(text_color="black")
        self.lcd_frame.voltage_label.configure(text=f"{set_voltage:05.2f}")
        self.lcd_frame.current_label.configure(text=f"{set_current:05.3f}")
        self.lcd_frame.power_label.configure(text="OFF")

    def _display_alarm_state(self) -> None:
        """Render the alternating alarm display and trigger the warning sound."""
        self.lcd_frame.cc_label.configure(text_color="black")
        self.lcd_frame.cv_label.configure(text_color="black")
        self.lcd_frame.voltage_label.configure(text="----")
        self.lcd_frame.power_label.configure(text="----")

        now = time.time()
        if now - self._last_alarm_toggle >= 0.3:
            self._blink_state = not self._blink_state
            self._last_alarm_toggle = now
            if self._blink_state and self.sound_enabled and self.sound is not None:
                self.sound.play()

        self.lcd_frame.current_label.configure(text="OCP" if self._blink_state else "")

    def open_graph_window(self) -> None:
        """Open and continuously refresh the Matplotlib history window."""
        if self._graph_figure is not None and plt.fignum_exists(self._graph_figure.number):
            self._graph_figure.canvas.manager.show()
            return

        if self.controller is None or len(self.controller.model.data_array) == 0:
            messagebox.showinfo("Graph", "No measurement data is available yet.")
            return

        log.info("Graph opened")
        self.killed = False
        self._graph_figure = plt.figure(num="Wanptek DC Power Supply")
        figure_manager = plt.get_current_fig_manager()
        if os.name == "nt":
            figure_manager.window.wm_iconbitmap(str(GRAPH_ICON_PATH))
        formatter = ticker.FuncFormatter(
            lambda value, _: time.strftime("%M:%S", time.gmtime(value))
        )

        axes = [self._graph_figure.add_subplot(3, 1, index + 1) for index in range(3)]
        labels = ("Voltage (V)", "Current (A)", "Power (W)")
        colors = ("b", "g", "r")
        data_columns = (1, 2, 3)

        def update(_frame) -> None:
            if self.killed or self.controller is None:
                return

            data = self.controller.model.data_array
            if len(data) == 0:
                return

            for axis, label, color, data_column in zip(axes, labels, colors, data_columns):
                axis.clear()
                axis.plot(data[:, 0], data[:, data_column], color, label=label)
                axis.grid()
                axis.legend(loc="lower left")
                axis.xaxis.set_major_formatter(formatter)
                axis.set_ylabel(label)

            axes[0].axhline(y=self.controller.model.set_voltage)
            axes[-1].set_xlabel("Time")
            self._graph_figure.tight_layout()

        self._graph_animation = FuncAnimation(
            self._graph_figure,
            update,
            interval=GRAPH_REFRESH_MS,
            cache_frame_data=False,
        )
        self._graph_figure.canvas.mpl_connect("close_event", lambda _event: self.close_graph_window())
        self._graph_figure.tight_layout()
        plt.show(block=False)

    def close_graph_window(self) -> None:
        """Request the graph loop to stop and close any open graph window."""
        self.killed = True
        if self._graph_animation is not None:
            event_source = getattr(self._graph_animation, "event_source", None)
            if event_source is not None:
                event_source.stop()
            self._graph_animation = None

        if self._graph_figure is not None:
            log.info("Graph closed")
            plt.close(self._graph_figure)
            self._graph_figure = None


class ToplevelWindow(customtkinter.CTkToplevel):
    """Dialog used to configure the serial communication settings."""

    def __init__(self, controller, *args, **kwargs) -> None:
        """Create the settings dialog and preload the current values when available."""
        super().__init__(*args, **kwargs)
        self.controller = controller

        self.geometry("300x180")
        self.title("Setup")
        self.focus()
        self.after(100, self.grab_set)

        port_list = [port.device for port in serial.tools.list_ports.comports()] or [""]
        device_address_list = [str(index) for index in range(32)]

        self.optionmenu_device_address = customtkinter.CTkOptionMenu(
            self,
            values=device_address_list,
        )
        self.optionmenu_device_address.grid(row=1, column=1, padx=2, pady=5, sticky="e")

        self.device_address_label = customtkinter.CTkLabel(self, text="Device Address ")
        self.device_address_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.optionmenu_serial_port_number = customtkinter.CTkOptionMenu(
            self,
            values=port_list,
        )
        self.optionmenu_serial_port_number.grid(
            row=2,
            column=1,
            padx=2,
            pady=5,
            sticky="e",
        )

        self.serial_port_number_label = customtkinter.CTkLabel(self, text="Serial Port ")
        self.serial_port_number_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.optionmenu_baudrate = customtkinter.CTkOptionMenu(
            self,
            values=["2400", "4800", "9600", "19200"],
        )
        self.optionmenu_baudrate.grid(row=3, column=1, padx=2, pady=5, sticky="e")

        self.baudrate_label = customtkinter.CTkLabel(self, text="Baud rate ")
        self.baudrate_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")

        self.save_button = customtkinter.CTkButton(self, text="Save", command=self.save_setup)
        self.save_button.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

        self._init_legacy_aliases()
        self._load_current_settings()

    def _init_legacy_aliases(self) -> None:
        """Expose legacy widget attribute names for compatibility."""
        self.optionmenuDeviceAddress = self.optionmenu_device_address
        self.optionmenuSerialPortNumber = self.optionmenu_serial_port_number
        self.optionmenuBaudrate = self.optionmenu_baudrate
        self.deviceAddressLabel = self.device_address_label
        self.SerialPortNumberLabel = self.serial_port_number_label
        self.BaudrateLabel = self.baudrate_label
        self.saveButton = self.save_button

    def _load_current_settings(self) -> None:
        """Populate the dialog with the currently persisted communication settings."""
        try:
            self.optionmenu_device_address.set(str(self.controller.model.device_address))
            self.optionmenu_serial_port_number.set(self.controller.model.serial_port)
            self.optionmenu_baudrate.set(str(self.controller.model.baudrate))
        except Exception:
            log.debug("Unable to preload current settings.", exc_info=True)

    def save_setup(self) -> None:
        """Persist dialog values, reconnect the controller, and close the dialog."""
        serial_port = self.optionmenu_serial_port_number.get().strip()
        baudrate = int(self.optionmenu_baudrate.get())
        device_address = int(self.optionmenu_device_address.get())

        if not serial_port:
            messagebox.showerror("Setup", "Please select a serial port.")
            return

        if not 0 <= device_address <= 31:
            messagebox.showerror("Setup", "Device address must be between 0 and 31.")
            return

        self.controller.model.serial_port = serial_port
        self.controller.model.baudrate = baudrate
        self.controller.model.device_address = device_address
        self.controller.model.save_settings()

        self.destroy()
        self.controller.connect()

    def saveSetup(self) -> None:
        """Backward-compatible wrapper around :meth:`save_setup`."""
        self.save_setup()
