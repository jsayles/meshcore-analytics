"""
Django management command to find connected MeshCore radios.

Usage:
    python manage.py find_usb_radio
    python manage.py find_usb_radio --save
"""

from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings

try:
    import serial.tools.list_ports  # type: ignore

    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class Command(BaseCommand):
    help = "Find connected MeshCore radios"

    def add_arguments(self, parser):
        parser.add_argument("--save", action="store_true", help="Save found radio port to .env file")

    def handle(self, *args, **options):
        if not SERIAL_AVAILABLE:
            self.stdout.write(self.style.ERROR("pyserial not installed. Install with: uv add pyserial"))
            return

        self.stdout.write(self.style.SUCCESS("\n🔍 Searching for USB serial devices...\n"))

        # List all serial ports
        ports = list(serial.tools.list_ports.comports())

        if not ports:
            self.stdout.write(self.style.WARNING("No USB serial devices found."))
            self.stdout.write("\nMake sure your MeshCore radio is:")
            self.stdout.write("  • Plugged in via USB")
            self.stdout.write("  • Powered on")
            self.stdout.write("  • Using a data-capable USB cable (not charge-only)")
            return

        # Display all ports
        self.stdout.write(f"Found {len(ports)} USB serial device(s):\n")

        likely_radios = []

        for i, port in enumerate(ports, 1):
            # Check if it looks like a MeshCore radio
            is_likely = self._is_likely_meshcore(port)

            marker = "✓" if is_likely else " "
            if is_likely:
                self.stdout.write(self.style.SUCCESS(f"   [{marker}] {port.device}"))
                likely_radios.append(port)
            else:
                self.stdout.write(self.style.WARNING(f"   [{marker}] {port.device}"))

            # Show description/manufacturer only if informative
            info_parts = []
            if port.manufacturer and port.manufacturer.lower() not in ["n/a", "unknown"]:
                info_parts.append(port.manufacturer)
            if port.description and port.description.lower() not in ["n/a", "unknown"]:
                info_parts.append(port.description)

            if info_parts:
                self.stdout.write(f"       * {' - '.join(info_parts)}")

        # Suggest likely candidates
        if likely_radios:
            self.stdout.write(self.style.SUCCESS(f"\n🎯 {len(likely_radios)} device(s) look like MeshCore radios:\n"))
            for port in likely_radios:
                self.stdout.write(self.style.SUCCESS(f"   {port.device}"))
        else:
            self.stdout.write(self.style.WARNING("\n⚠️  No obvious MeshCore radios found. Try testing each device manually."))

        # Show .env update instructions
        if likely_radios:
            primary = likely_radios[0]
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS("📝 To use this radio:\n"))
            self.stdout.write("1. Update your .env file:")
            self.stdout.write(f"   SERIAL_PORT={primary.device}\n")
            self.stdout.write("2. Restart your server:")
            self.stdout.write("   uv run daphne -b 0.0.0.0 -p 8000 max.asgi:application")

            if options["save"]:
                self.update_env_file(primary.device)

    def _is_likely_meshcore(self, port):
        """
        Heuristic to detect if a port is likely a MeshCore radio.

        Adjust these patterns based on your actual hardware.
        """
        device = port.device.lower()
        desc = port.description.lower()
        manufacturer = (port.manufacturer or "").lower()

        # Common patterns for MeshCore radios
        patterns = [
            "meshcore" in desc,
            "meshcore" in manufacturer,
            "esp32" in desc,
            "espressif" in manufacturer,  # Espressif makes ESP32 chips
            "cp210" in desc,  # Common USB-UART chip
            "ch340" in desc,  # Common USB-UART chip
            "ftdi" in desc,  # FTDI USB-UART
            "usb jtag" in desc,  # ESP32 USB JTAG/serial debug unit
            "/dev/cu.usbmodem" in device,  # Mac pattern (cu)
            "/dev/tty.usbmodem" in device,  # Mac pattern (tty)
            "/dev/ttyacm" in device,  # Linux pattern
            "/dev/ttyusb" in device,  # Linux pattern
        ]

        return any(patterns)

    def update_env_file(self, port):
        """Update .env file with the found port."""

        env_path = Path(settings.BASE_DIR) / ".env"

        try:
            # Read existing .env
            if env_path.exists():
                with open(env_path) as f:
                    lines = f.readlines()

                # Update SERIAL_PORT line
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith("SERIAL_PORT="):
                        lines[i] = f"SERIAL_PORT={port}\n"
                        updated = True

                if not updated:
                    lines.append(f"\nSERIAL_PORT={port}\n")

                with open(env_path, "w") as f:
                    f.writelines(lines)

                self.stdout.write(self.style.SUCCESS(f"\n✓ Updated {env_path}"))
            else:
                self.stdout.write(self.style.WARNING(f"\n⚠ .env file not found at {env_path}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Failed to update .env: {e}"))
