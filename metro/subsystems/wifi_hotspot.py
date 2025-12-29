"""
WiFi hotspot management with platform-specific implementations.

Provides cross-platform WiFi hotspot configuration with full support on Linux
(via NetworkManager) and limited database-only support on macOS.
"""

import logging
import platform
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


class UnsupportedPlatformError(Exception):
    """Raised when WiFi management is not supported on the current platform."""

    pass


class BaseWiFiManager(ABC):
    """Abstract base class for platform-specific WiFi management."""

    def can_scan(self) -> bool:
        """
        Check if network scanning is supported.
        Default implementation: try scan_networks() and catch NotImplementedError.
        """
        try:
            # Try to scan - if it raises NotImplementedError, scanning not supported
            self.scan_networks()
            return True
        except NotImplementedError:
            return False
        except Exception:
            # Other errors mean scanning is supported but failed
            return True

    @abstractmethod
    def scan_networks(self) -> list[dict]:
        """Scan for available networks."""
        pass

    @abstractmethod
    def configure(self, ssid: str, password: str) -> bool:
        """Configure WiFi hotspot."""
        pass

    @abstractmethod
    def connect(self) -> bool:
        """Connect to configured hotspot."""
        pass

    @abstractmethod
    def check_status(self) -> dict:
        """Check connection status."""
        pass


class LinuxWiFiManager(BaseWiFiManager):
    """WiFi management using NetworkManager (nmcli) on Linux."""

    def scan_networks(self) -> list[dict]:
        """
        Scan for available WiFi networks using nmcli.

        Returns:
            List of dicts with keys: ssid, signal, security
            Sorted by signal strength (strongest first)

        Raises:
            RuntimeError: If scan fails or times out
        """
        try:
            # Rescan for fresh results (don't fail if rescan doesn't work)
            subprocess.run(
                ["nmcli", "dev", "wifi", "rescan"],
                capture_output=True,
                timeout=5,
                check=False,
                start_new_session=True,
            )

            # Get scan results: SSID, SIGNAL, SECURITY
            result = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
                start_new_session=True,
            )

            networks = []
            seen_ssids = set()

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split(":")
                if len(parts) >= 3:
                    ssid = parts[0]
                    # Skip empty SSIDs and duplicates
                    if ssid and ssid not in seen_ssids:
                        seen_ssids.add(ssid)
                        try:
                            signal = int(parts[1])
                        except ValueError:
                            signal = 0
                        security = parts[2]
                        networks.append({"ssid": ssid, "signal": signal, "security": security})

            # Sort by signal strength descending
            networks.sort(key=lambda x: x["signal"], reverse=True)
            logger.info(f"Scanned {len(networks)} WiFi networks")
            return networks

        except subprocess.TimeoutExpired:
            logger.error("WiFi scan timed out")
            raise RuntimeError("WiFi scan timed out")
        except subprocess.CalledProcessError as e:
            logger.error(f"WiFi scan failed: {e.stderr}")
            raise RuntimeError(f"WiFi scan failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error during WiFi scan: {e}")
            raise RuntimeError(f"WiFi scan error: {str(e)}")

    def configure(self, ssid: str, password: str) -> bool:
        """
        Configure NetworkManager connection for phone hotspot.

        Creates or updates 'phone-hotspot' connection profile with the provided
        SSID and password. Sets auto-connect priority to 10.

        Args:
            ssid: WiFi network SSID
            password: WiFi network password

        Returns:
            True if successful

        Raises:
            RuntimeError: If configuration fails or times out
        """
        try:
            # Delete existing connection if it exists
            logger.info("Removing existing phone-hotspot connection (if any)")
            subprocess.run(
                ["nmcli", "connection", "delete", "phone-hotspot"],
                capture_output=True,
                timeout=5,
                check=False,
                start_new_session=True,
            )

            # Create new connection
            logger.info(f"Creating phone-hotspot connection for SSID: {ssid}")
            subprocess.run(
                [
                    "nmcli",
                    "connection",
                    "add",
                    "con-name",
                    "phone-hotspot",
                    "ifname",
                    "wlan0",
                    "type",
                    "wifi",
                    "ssid",
                    ssid,
                    "wifi-sec.key-mgmt",
                    "wpa-psk",
                    "wifi-sec.psk",
                    password,
                    "connection.autoconnect",
                    "yes",
                    "connection.autoconnect-priority",
                    "10",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
                start_new_session=True,
            )

            logger.info("phone-hotspot connection configured successfully")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Hotspot configuration timed out")
            raise RuntimeError("Configuration timed out")
        except subprocess.CalledProcessError as e:
            logger.error(f"Hotspot configuration failed: {e.stderr}")
            raise RuntimeError(f"Configuration failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error configuring hotspot: {e}")
            raise RuntimeError(f"Configuration error: {str(e)}")

    def connect(self) -> bool:
        """
        Attempt to connect to the configured phone-hotspot.

        Returns:
            True if successful

        Raises:
            RuntimeError: If connection fails or times out
        """
        try:
            logger.info("Attempting to connect to phone-hotspot")
            subprocess.run(
                ["nmcli", "connection", "up", "phone-hotspot"],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
                start_new_session=True,
            )
            logger.info("Connected to phone-hotspot successfully")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Hotspot connection timed out")
            raise RuntimeError("Connection timed out - network may not be in range")
        except subprocess.CalledProcessError as e:
            logger.error(f"Hotspot connection failed: {e.stderr}")
            raise RuntimeError(f"Connection failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to hotspot: {e}")
            raise RuntimeError(f"Connection error: {str(e)}")

    def check_status(self) -> dict:
        """
        Check if phone-hotspot is currently connected.

        Returns:
            Dict with keys:
                - connected: bool (True if connected)
                - ssid: str (SSID if connected, None otherwise)
                - error: str (error message if not connected, None otherwise)
                - platform_support: bool (True for Linux)
                - last_check: str (ISO timestamp of check)
        """
        try:
            # Get active connections
            result = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,STATE", "connection", "show", "--active"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
                start_new_session=True,
            )

            # Check if phone-hotspot is in active connections
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split(":")
                if len(parts) >= 2:
                    name = parts[0]
                    state = parts[1]
                    if name == "phone-hotspot" and "activated" in state:
                        # Get SSID from connection details
                        ssid_result = subprocess.run(
                            ["nmcli", "-t", "-f", "802-11-wireless.ssid", "connection", "show", "phone-hotspot"],
                            capture_output=True,
                            text=True,
                            timeout=5,
                            check=True,
                            start_new_session=True,
                        )
                        ssid = ssid_result.stdout.strip().split(":")[-1] if ssid_result.stdout else "Unknown"

                        return {
                            "connected": True,
                            "ssid": ssid,
                            "error": None,
                            "platform_support": True,
                            "last_check": datetime.now().isoformat(),
                        }

            # Not connected
            return {
                "connected": False,
                "ssid": None,
                "error": "Hotspot not connected",
                "platform_support": True,
                "last_check": datetime.now().isoformat(),
            }

        except subprocess.TimeoutExpired:
            logger.error("Hotspot status check timed out")
            return {
                "connected": False,
                "ssid": None,
                "error": "Status check timed out",
                "platform_support": True,
                "last_check": datetime.now().isoformat(),
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Hotspot status check failed: {e.stderr}")
            return {
                "connected": False,
                "ssid": None,
                "error": f"Status check failed: {e.stderr}",
                "platform_support": True,
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Unexpected error checking hotspot status: {e}")
            return {
                "connected": False,
                "ssid": None,
                "error": f"Status check error: {str(e)}",
                "platform_support": True,
                "last_check": datetime.now().isoformat(),
            }


class MacWiFiManager(BaseWiFiManager):
    """WiFi management for macOS - database only, no network control."""

    def scan_networks(self) -> list[dict]:
        """
        Network scanning not supported on macOS.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("Network scanning not supported on macOS")

    def configure(self, ssid: str, password: str) -> bool:
        """
        No-op configuration for macOS - database handles storage.

        Args:
            ssid: WiFi network SSID
            password: WiFi network password

        Returns:
            True (configuration saved to database only)
        """
        logger.info(f"WiFi config saved to database for SSID: {ssid} (macOS - no NetworkManager control)")
        return True

    def connect(self) -> bool:
        """
        Auto-connect not supported on macOS.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("Auto-connect not supported on macOS - please connect manually in System Settings")

    def check_status(self) -> dict:
        """
        Check connection status - limited support on macOS.

        Returns:
            Dict indicating platform does not support status checking
        """
        return {
            "connected": False,
            "ssid": None,
            "error": "Platform does not support status checking",
            "platform_support": False,
            "last_check": datetime.now().isoformat(),
        }


def get_wifi_manager() -> BaseWiFiManager:
    """
    Get the appropriate WiFi manager for the current platform.

    Returns:
        BaseWiFiManager: Platform-specific WiFi manager instance

    Raises:
        UnsupportedPlatformError: If platform is not supported
    """
    system = platform.system()
    if system == "Linux":
        logger.info("Using LinuxWiFiManager (NetworkManager/nmcli)")
        return LinuxWiFiManager()
    elif system == "Darwin":  # macOS
        logger.info("Using MacWiFiManager (limited - database only)")
        return MacWiFiManager()
    else:
        # Windows or others - not supported
        raise UnsupportedPlatformError(
            f"WiFi hotspot management not supported on {system}. "
            f"Supported platforms: Linux (with NetworkManager), macOS (limited)"
        )
