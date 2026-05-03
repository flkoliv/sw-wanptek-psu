import logging
import time
from threading import Event, Thread

import serial as _serial
from pymodbus import FramerType
from pymodbus.client import ModbusSerialClient as ModbusClient

log = logging.getLogger(__name__)

# pymodbus 3.9+ triggers exclusive port locking via pyserial (TIOCEXCL)
# which fails with EAGAIN on some Linux systems. Force exclusive=False
# so pyserial never attempts the exclusive lock.
_orig_serial_open = _serial.Serial.open


def _non_exclusive_open(self) -> None:
    self._exclusive = False
    _orig_serial_open(self)


_serial.Serial.open = _non_exclusive_open

# pymodbus renamed the device-address parameter across versions:
# 3.8.x: slave=   3.9-3.12: unit=   3.13+: dev_id=
# Detect the correct name at first call and cache it.
_SLAVE_PARAM: str = ""


def _with_dev(method, device_address: int, **kwargs):
    """Call a pymodbus method using the correct device-address keyword."""
    global _SLAVE_PARAM
    if _SLAVE_PARAM:
        return method(**kwargs, **{_SLAVE_PARAM: device_address})
    for name in ("slave", "dev_id", "unit"):
        try:
            result = method(**kwargs, **{name: device_address})
            _SLAVE_PARAM = name
            return result
        except TypeError:
            continue
    return method(**kwargs)

READ_ADDRESS = 0x00
READ_REGISTER_COUNT = 8
REFRESH_DELAY_SECONDS = 0.1
RECONNECT_INTERVAL_SECONDS = 3.0
SERIAL_TIMEOUT_SECONDS = 0.2


class PSUController:
    """Coordinate Modbus communication between the model and the UI."""

    def __init__(self, model, view) -> None:
        """Initialize the controller and attempt the first connection."""
        self.model = model
        self.view = view
        self.client = None
        self._thread = None
        self._stop_event = Event()
        self._last_reconnect_attempt = 0.0

        self.out_button_pushed = False
        self.ocp_button_pushed = False
        self.lock_button_pushed = False
        self.connected = False
        self.connection_error = "Not connected"

        self.connect()

    def start(self) -> None:
        """Start the communication thread."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop polling and close the Modbus client."""
        self._stop_event.set()
        self.connected = False
        self.connection_error = ""
        self.close_client()

        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _run_loop(self) -> None:
        """Run the communication loop in the background."""
        while not self._stop_event.is_set():
            if self.connected:
                self.read_data()
                if self._stop_event.is_set():
                    break
                self._sync_knobs()
                self._handle_button_presses()
            else:
                self._attempt_reconnect_if_needed()

            if self._stop_event.is_set():
                break

            self.view.schedule_display_update(
                self.connected,
                self.model.out_on,
                self.model.ocp_on,
                self.model.keyboard_locked,
                self.model.constant_current,
                self.model.alarm,
                self.model.real_voltage,
                self.model.real_current,
                self.model.set_voltage,
                self.model.set_current,
                self.model.max_voltage,
                self.model.max_current,
            )
            time.sleep(REFRESH_DELAY_SECONDS)

    def connect(self) -> bool:
        """Open the Modbus serial connection."""
        if not self.model.has_valid_connection_settings():
            self.connection_error = "Configure serial settings"
            self._mark_disconnected(log_error=False)
            return False

        self.close_client()

        try:
            log.info("Connecting to %s", self.model.serial_port)
            client = ModbusClient(
                port=self.model.serial_port,
                framer=FramerType.RTU,
                baudrate=self.model.baudrate,
                timeout=SERIAL_TIMEOUT_SECONDS,
                parity="N",
            )
            if not client.connect():
                raise ConnectionError("Serial connection could not be opened.")

            response = _with_dev(
                client.read_holding_registers,
                self.model.device_address,
                address=READ_ADDRESS,
                count=READ_REGISTER_COUNT,
            )
            if response.isError():
                raise ConnectionError(f"Device did not respond: {response}")

            self.client = client
            self.connected = True
            self.connection_error = ""
            log.info("Connected to %s", self.model.serial_port)
            self.view.schedule_status_update("Connected", "green", buttons_enabled=True)
            return True
        except Exception as exc:
            self.connection_error = str(exc)
            log.error("Connection failed: %s", exc)
            self._mark_disconnected(log_error=False)
            return False

    def close_client(self) -> None:
        """Close the current Modbus client if one is open."""
        if self.client is None:
            return

        try:
            self.client.close()
        except Exception:
            log.debug("Error while closing Modbus client.", exc_info=True)
        finally:
            self.client = None

    def _attempt_reconnect_if_needed(self) -> None:
        """Try to reconnect periodically when valid settings are available."""
        if not self.model.has_valid_connection_settings():
            self.view.schedule_status_update(
                "Configure serial settings",
                "orange",
                buttons_enabled=False,
            )
            return

        now = time.time()
        if now - self._last_reconnect_attempt < RECONNECT_INTERVAL_SECONDS:
            return

        self._last_reconnect_attempt = now
        self.connect()

    def _mark_disconnected(self, log_error: bool = True) -> None:
        """Update the model and UI after a disconnect or failed I/O."""
        if log_error and self.connection_error:
            log.error("Disconnected: %s", self.connection_error)
        elif self.connection_error:
            log.info("Disconnected: %s", self.connection_error)

        self.connected = False
        self.close_client()
        self.model.reset_measurements()
        self.view.schedule_set_disabled()
        self.view.schedule_status_update(
            self.connection_error or "Disconnected",
            "red",
            buttons_enabled=False,
        )

    def _sync_knobs(self) -> None:
        """Send knob changes to the device when software control is enabled."""
        if not self.model.keyboard_locked:
            return

        voltage_value = self.view.knob_frame.voltageKnob.get()
        current_value = self.view.knob_frame.currentKnob.get()

        if self.model.set_voltage != voltage_value:
            self.model.set_voltage = voltage_value
            self.model.clamp_setpoints()
            self.write_data()

        if self.model.set_current != current_value:
            self.model.set_current = current_value
            self.model.clamp_setpoints()
            self.write_data()

    def _handle_button_presses(self) -> None:
        """Apply pending button actions from the UI and write them to the PSU."""
        if self.out_button_pushed:
            self.model.out_on = not self.model.out_on
            log.info("Output %s", "ON" if self.model.out_on else "OFF")
            self.write_data()
            self.out_button_pushed = False

        if self.ocp_button_pushed:
            self.model.ocp_on = not self.model.ocp_on
            log.info("OCP %s", "ON" if self.model.ocp_on else "OFF")
            self.write_data()
            self.ocp_button_pushed = False

        if self.lock_button_pushed:
            self.model.keyboard_locked = not self.model.keyboard_locked
            log.info(
                "Software control %s",
                "ENABLED" if self.model.keyboard_locked else "DISABLED",
            )
            self.write_data()
            self.lock_button_pushed = False

    def read_data(self) -> None:
        """Read the device registers and update the model with decoded values."""
        try:
            if self._stop_event.is_set() or self.client is None:
                return

            response = _with_dev(
                self.client.read_holding_registers,
                self.model.device_address,
                address=READ_ADDRESS,
                count=READ_REGISTER_COUNT,
            )
            if response.isError():
                raise ConnectionError(f"Modbus read error: {response}")

            regs = response.registers  # 8 x uint16, big-endian decoded

            status_byte = (regs[0] >> 8) & 0xFF
            voltage_byte = regs[0] & 0xFF
            current_byte = (regs[1] >> 8) & 0xFF

            status_bits = f"{status_byte:08b}"
            voltage_bits = f"{voltage_byte:08b}"
            current_bits = f"{current_byte:08b}"

            self.model.out_on = status_bits[-1] == "1"
            self.model.ocp_on = status_bits[-2] == "1"
            endian = "big" if status_bits[-4] == "1" else "little"
            self.model.endian = endian
            self.model.constant_current = status_bits[-5] == "1"
            self.model.alarm = status_bits[-6] == "1"

            decimal_voltage = 0.1 if voltage_bits[0] == "1" else 0.01
            decimal_current = 0.01 if current_bits[0] == "1" else 0.001

            def _reg(r: int) -> int:
                if endian == "big":
                    return r
                return ((r & 0xFF) << 8) | ((r >> 8) & 0xFF)

            self.model.real_voltage = round(_reg(regs[2]) * decimal_voltage, 2)
            self.model.real_current = round(_reg(regs[3]) * decimal_current, 3)
            self.model.set_voltage = round(_reg(regs[4]) * decimal_voltage, 2)
            self.model.set_current = round(_reg(regs[5]) * decimal_current, 3)
            self.model.max_voltage = round(_reg(regs[6]) * decimal_voltage, 2)
            self.model.max_current = round(_reg(regs[7]) * decimal_current, 3)
            self.model.clamp_setpoints()
            self.model.update_data_array()
            self.connected = True
            self.connection_error = ""
            self.view.schedule_status_update("Connected", "green", buttons_enabled=True)
        except Exception as exc:
            if self._stop_event.is_set():
                return

            self.connection_error = str(exc)
            log.error("Read error: %s", exc)
            self._mark_disconnected(log_error=False)

    def write_data(self) -> None:
        """Write the current setpoints to the device via Modbus FC16."""
        try:
            if self._stop_event.is_set() or not self.client:
                raise ConnectionError("No active Modbus client.")

            self.model.clamp_setpoints()

            status_byte = int(
                f"00000{int(self.model.keyboard_locked)}"
                f"{int(self.model.ocp_on)}{int(self.model.out_on)}",
                2,
            )
            volt_raw = int(round(self.model.set_voltage * 100))
            curr_raw = int(round(self.model.set_current * 1000))

            # PSU expects little-endian byte order inside each register
            def _swap(v: int) -> int:
                return ((v & 0xFF) << 8) | ((v >> 8) & 0xFF)

            _with_dev(
                self.client.write_registers,
                self.model.device_address,
                address=0,
                values=[status_byte << 8, _swap(volt_raw), _swap(curr_raw)],
            )
        except Exception as exc:
            if self._stop_event.is_set():
                return

            self.connection_error = str(exc)
            log.error("Write error: %s", exc)
            self._mark_disconnected(log_error=False)
