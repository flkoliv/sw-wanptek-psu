import logging
import pickle
import time
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)

PARAM_PATH = Path("./param")
GRAPH_HISTORY_SECONDS = 600
DEFAULT_BAUDRATE = 9600
MIN_DEVICE_ADDRESS = 0
MAX_DEVICE_ADDRESS = 31


class PSUModel:
    """Store the current PSU state and the user connection settings."""

    def __init__(self) -> None:
        self.out_on = False
        self.ocp_on = False
        self.keyboard_locked = False
        self.endian = "little"
        self.constant_current = False
        self.alarm = False

        self.real_voltage = 0.0
        self.real_current = 0.0
        self.set_voltage = 0.0
        self.set_current = 0.0
        self.max_voltage = 0.0
        self.max_current = 0.0

        self.data_array = np.empty((0, 4))
        self.time_origin = time.time()

        self.serial_port = ""
        self.baudrate = DEFAULT_BAUDRATE
        self.device_address = MIN_DEVICE_ADDRESS
        self.load_settings()

    @property
    def serialPort(self) -> str:
        """Return the configured serial port using the legacy attribute name."""
        return self.serial_port

    @serialPort.setter
    def serialPort(self, value: str) -> None:
        """Set the configured serial port using the legacy attribute name."""
        self.serial_port = value

    @property
    def deviceAddress(self) -> int:
        """Return the device address using the legacy attribute name."""
        return self.device_address

    @deviceAddress.setter
    def deviceAddress(self, value: int) -> None:
        """Set the device address using the legacy attribute name."""
        self.device_address = value

    def load_settings(self) -> None:
        """Load persisted communication settings from the local parameter file."""
        try:
            with PARAM_PATH.open("rb") as file:
                self.serial_port = pickle.load(file)
                self.baudrate = pickle.load(file)
                self.device_address = pickle.load(file)
        except (FileNotFoundError, EOFError, pickle.PickleError):
            log.info("No saved connection settings found")

    def save_settings(self) -> None:
        """Persist the current communication settings to the local parameter file."""
        with PARAM_PATH.open("wb") as file:
            pickle.dump(self.serial_port, file)
            pickle.dump(self.baudrate, file)
            pickle.dump(self.device_address, file)
        log.info(
            "Settings saved: %s, %s baud, address %s",
            self.serial_port,
            self.baudrate,
            self.device_address,
        )

    def has_valid_connection_settings(self) -> bool:
        """Return whether the model contains enough information to connect."""
        return bool(self.serial_port) and self.baudrate > 0 and (
            MIN_DEVICE_ADDRESS <= self.device_address <= MAX_DEVICE_ADDRESS
        )

    def clamp_setpoints(self) -> None:
        """Clamp requested voltage and current to the device reported limits."""
        if self.max_voltage > 0:
            self.set_voltage = min(max(self.set_voltage, 0.0), self.max_voltage)
        else:
            self.set_voltage = max(self.set_voltage, 0.0)

        if self.max_current > 0:
            self.set_current = min(max(self.set_current, 0.0), self.max_current)
        else:
            self.set_current = max(self.set_current, 0.0)

    def reset_measurements(self) -> None:
        """Reset transient measurements after a disconnect or failed read."""
        self.real_voltage = 0.0
        self.real_current = 0.0
        self.constant_current = False
        self.alarm = False

    def update_data_array(self) -> None:
        """Store the last 10 minutes of voltage, current and power data."""
        elapsed = time.time() - self.time_origin
        new_row = np.array(
            [[elapsed, self.real_voltage, self.real_current, self.get_real_power()]]
        )
        self.data_array = np.append(self.data_array, new_row, axis=0)

        while len(self.data_array) and elapsed - self.data_array[0, 0] > GRAPH_HISTORY_SECONDS:
            self.data_array = np.delete(self.data_array, 0, axis=0)

    def update_values(
        self,
        output_on: bool,
        ocp_on: bool,
        keyboard_locked: bool,
        endian: str,
        constant_current: bool,
        alarm_triggered: bool,
        real_voltage: float,
        real_current: float,
        set_voltage: float,
        set_current: float,
        max_voltage: float,
        max_current: float,
    ) -> None:
        """Update the full device state from values decoded by the controller."""
        self.out_on = output_on
        self.ocp_on = ocp_on
        self.keyboard_locked = keyboard_locked
        self.endian = endian
        self.constant_current = constant_current
        self.alarm = alarm_triggered
        self.real_voltage = real_voltage
        self.real_current = real_current
        self.set_voltage = set_voltage
        self.set_current = set_current
        self.max_voltage = max_voltage
        self.max_current = max_current

    def is_output_on(self) -> bool:
        """Return whether the PSU output is currently enabled."""
        return self.out_on

    def is_ocp_on(self) -> bool:
        """Return whether over-current protection is enabled."""
        return self.ocp_on

    def is_keyboard_locked(self) -> bool:
        """Return whether remote control is enabled through the software."""
        return self.keyboard_locked

    def get_endian(self) -> str:
        """Return the byte order reported by the device."""
        return self.endian

    def is_constant_current(self) -> bool:
        """Return whether the PSU is currently regulating in constant current mode."""
        return self.constant_current

    def is_alarm_triggered(self) -> bool:
        """Return whether the PSU currently reports an alarm state."""
        return self.alarm

    def get_real_voltage(self) -> float:
        """Return the measured output voltage."""
        return self.real_voltage

    def get_real_current(self) -> float:
        """Return the measured output current."""
        return self.real_current

    def get_real_power(self) -> float:
        """Return the measured output power."""
        return self.real_voltage * self.real_current

    def get_set_voltage(self) -> float:
        """Return the configured voltage setpoint."""
        return self.set_voltage

    def get_set_current(self) -> float:
        """Return the configured current setpoint."""
        return self.set_current

    def get_max_voltage(self) -> float:
        """Return the maximum voltage supported by the connected PSU."""
        return self.max_voltage

    def get_max_current(self) -> float:
        """Return the maximum current supported by the connected PSU."""
        return self.max_current
