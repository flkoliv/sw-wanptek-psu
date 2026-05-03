# Wanptek PSU Controller

Desktop application to control a Wanptek DC power supply via USB / serial port.
Compatible with Windows, macOS and Linux.

Features:

- Display voltage, current and power in real time
- Adjust voltage and current setpoints
- Enable or disable the output
- Enable or disable OCP (over-current protection)
- Plot measurement history in a live graph window

## Interface

The application uses a `customtkinter` interface with:

- An LCD-style main display
- Two adjustment knobs
- A button bar for Menu, Graph, Lock, OCP and Output control

## Requirements

- Python 3.10 or later with `tkinter` available
- A compatible Wanptek DC power supply
- A USB-to-serial adapter recognised by your OS

---

## Installation

### Recommended — via pip (all platforms)

```bash
pip install wanptek-controller
wanptek-controller
```

### From source

Clone the repository and install in a virtual environment:

```bash
git clone https://github.com/flkoliv/sw-wanptek-psu.git
cd sw-wanptek-psu
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.\.venv\Scripts\Activate.ps1  # Windows (PowerShell)
pip install -e .
wanptek-controller
```

---

## Platform notes

### Windows

- Install Python 3.10 from the official installer and make sure **tcl/tk and IDLE** is checked
- If PowerShell blocks script execution: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
- Serial ports appear as `COM3`, `COM4`, ...

### macOS

- Install Python and tkinter via Homebrew:
  ```bash
  brew install python@3.10 python-tk@3.10
  ```
- Serial ports appear as `/dev/cu.usbserial-XXXX` or `/dev/cu.SLAB_USBtoUART`

### Linux

- Install Python and tkinter:
  ```bash
  # Debian / Ubuntu
  sudo apt install python3.10 python3.10-venv python3-tk

  # Fedora
  sudo dnf install python3.10 python3-tkinter
  ```
- Add your user to the `dialout` group to access the serial port:
  ```bash
  sudo usermod -aG dialout $USER
  ```
  Log out and back in for the change to take effect.
- Serial ports appear as `/dev/ttyUSB0`, `/dev/ttyACM0`, ...

---

## First-time setup

On first launch:

1. Click **Menu**
2. Select the serial port connected to your power supply
3. Select the Modbus device address
4. Select the baud rate
5. Click **Save**

The application will then attempt to connect automatically.

Settings are saved to `~/.wanptek_controller/param`.

---

## Usage

### Main display

Shows:

- Output voltage
- Output current
- Output power
- OCP status
- Output status

### Buttons

- **Menu** — open the serial configuration dialog
- **Graph** — open the measurement history window
- **Lock** — enable or disable software control of the setpoints
- **OCP** — toggle over-current protection
- **OUT** — enable or disable the PSU output

### Voltage / current adjustment

When **Lock** is active:

- The knobs become interactive
- New values are sent to the power supply

When **Lock** is inactive:

- The knobs display the current setpoints read-only

### Graph

The **Graph** window shows the last 10 minutes of:

- Voltage
- Current
- Power

---

## Project structure

```
wanptek_controller/
├── main.py          — application entry point
├── PSUModel.py      — state and persisted settings
├── PSUController.py — Modbus communication and control logic
├── PSUView.py       — graphical interface
├── images/          — icons and logo
└── ressources/      — fonts and sounds
main.py              — development shim (calls wanptek_controller.main)
run.pyw              — GUI launcher (no console window on Windows)
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'tkinter'`

Your Python installation does not include Tk.

- **Windows** — reinstall Python 3.10 with **tcl/tk and IDLE** checked
- **macOS** — `brew install python-tk@3.10`
- **Linux** — `sudo apt install python3-tk` (or equivalent)

### PowerShell blocks `Activate.ps1` (Windows)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Serial port permission denied (Linux)

```bash
sudo usermod -aG dialout $USER
```

Log out and back in.

### Application does not connect

- Check that the correct serial port is selected
- Check that the Modbus address matches the device
- Make sure the power supply is switched on
- Check the USB-to-serial cable and driver

### Graph window does not open

The graph only opens once at least one measurement has been received.

---

## License

See [LICENSE](LICENSE).
