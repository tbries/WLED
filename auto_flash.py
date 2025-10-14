#!/usr/bin/env python3
"""
WLED Auto-Flasher for GitHub Universe '25 Demo

This script continuously monitors for new ESP8266/ESP32 devices connected via USB
and automatically flashes them with the WLED firmware. It supports flashing
multiple devices simultaneously without blocking the detection loop.

The script automatically detects device type and uses the appropriate PlatformIO environment:
- ESP8266 devices: uses 'esp8266_2m' environment
- ESP32 devices: uses 'esp32dev' environment

Usage:
    python3 auto_flash.py

Requirements:
    - PlatformIO must be installed and available in PATH
    - WLED project must be built (run 'npm run build' first)
    - ESP8266/ESP32 devices connected via USB serial adapters
"""

import subprocess
import threading
import time
import re
import sys
from datetime import datetime
from typing import Set, Dict, Optional, List
from dataclasses import dataclass


@dataclass
class Device:
    """Represents a connected USB serial device."""
    port: str
    hardware_id: str
    description: str
    location: str
    device_type: str = "unknown"  # "esp8266", "esp32", or "unknown"


class WLEDAutoFlasher:
    def __init__(self, scan_interval: float = 2.0):
        """
        Initialize the auto-flasher.
        
        Args:
            scan_interval: Time in seconds between device scans
        """
        self.scan_interval = scan_interval
        self.processed_devices: Set[str] = set()
        self.active_flashes: Dict[str, threading.Thread] = {}
        self.flash_lock = threading.Lock()
        self.running = False
        
        # Statistics
        self.total_attempts = 0
        self.successful_flashes = 0
        self.failed_flashes = 0
        
        print("🚀 WLED Auto-Flasher for GitHub Universe '25")
        print("=" * 60)
        print("Monitoring for new ESP8266/ESP32 devices...")
        print("Press Ctrl+C to stop")
        print()

    def get_connected_devices(self) -> List[Device]:
        """
        Get list of connected USB serial devices using PlatformIO.
        
        Returns:
            List of Device objects representing connected devices
        """
        try:
            result = subprocess.run(
                ["pio", "device", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"❌ Error running 'pio device list': {result.stderr}")
                return []
                
            return self._parse_device_list(result.stdout)
            
        except subprocess.TimeoutExpired:
            print("⚠️  Timeout while scanning devices")
            return []
        except FileNotFoundError:
            print("❌ PlatformIO not found. Please install PlatformIO first.")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error scanning devices: {e}")
            return []

    def _parse_device_list(self, output: str) -> List[Device]:
        """
        Parse the output of 'pio device list' command.
        
        Args:
            output: Raw output from pio device list
            
        Returns:
            List of parsed Device objects
        """
        devices = []
        lines = output.strip().split('\n')
        
        current_port = None
        current_hw_id = None
        current_desc = None
        current_location = None
        
        for line in lines:
            line = line.strip()
            
            # Look for port lines (start with /dev/)
            if line.startswith('/dev/'):
                # Save previous device if we have one
                if current_port and self._is_esp_device(current_hw_id, current_desc):
                    device_type = self._detect_device_type(current_hw_id, current_desc)
                    devices.append(Device(
                        port=current_port,
                        hardware_id=current_hw_id or "",
                        description=current_desc or "",
                        location=current_location or "",
                        device_type=device_type
                    ))
                
                # Start new device
                current_port = line
                current_hw_id = None
                current_desc = None
                current_location = None
                
            elif line.startswith("Hardware ID:"):
                current_hw_id = line.replace("Hardware ID:", "").strip()
                # Extract location if present
                if "LOCATION=" in current_hw_id:
                    location_match = re.search(r'LOCATION=([^\s]+)', current_hw_id)
                    if location_match:
                        current_location = location_match.group(1)
                        
            elif line.startswith("Description:"):
                current_desc = line.replace("Description:", "").strip()
        
        # Don't forget the last device
        if current_port and self._is_esp_device(current_hw_id, current_desc):
            device_type = self._detect_device_type(current_hw_id, current_desc)
            devices.append(Device(
                port=current_port,
                hardware_id=current_hw_id or "",
                description=current_desc or "",
                location=current_location or "",
                device_type=device_type
            ))
            
        return devices

    def _is_esp_device(self, hardware_id: Optional[str], description: Optional[str]) -> bool:
        """
        Determine if a device is likely an ESP8266/ESP32 based on hardware ID and description.
        
        Args:
            hardware_id: Hardware ID string from device list
            description: Description string from device list
            
        Returns:
            True if device appears to be an ESP development board
        """
        if not hardware_id and not description:
            return False
            
        # Common USB-to-serial chip vendor IDs used in ESP boards
        esp_vendor_ids = [
            "1A86:7523",  # CH340/CH341 (very common in ESP8266 boards)
            "10C4:EA60",  # CP2102/CP2104 (Silicon Labs)
            "0403:6001",  # FTDI FT232
            "0403:6014",  # FTDI FT232H
        ]
        
        # Check hardware ID
        if hardware_id:
            for vid_pid in esp_vendor_ids:
                if vid_pid in hardware_id:
                    return True
        
        # Check description for common terms
        if description:
            esp_terms = ["usb serial", "uart", "ch340", "cp210", "ftdi"]
            desc_lower = description.lower()
            for term in esp_terms:
                if term in desc_lower:
                    return True
        
        return False

    def _detect_device_type(self, hardware_id: Optional[str], description: Optional[str]) -> str:
        """
        Detect if a device is ESP8266 or ESP32 based on hardware ID and description.
        
        Args:
            hardware_id: Hardware ID string from device list
            description: Description string from device list
            
        Returns:
            "esp8266", "esp32", or "unknown"
        """
        if not hardware_id and not description:
            return "unknown"
        
        # For now, we'll use a simple heuristic:
        # - Most cheap development boards with CH340 are ESP8266
        # - ESP32 often uses CP210x or has "ESP32" in description
        # - This can be refined based on more specific hardware patterns
        
        hardware_lower = (hardware_id or "").lower()
        desc_lower = (description or "").lower()
        
        # Check for ESP32 indicators first
        if "esp32" in desc_lower or "esp32" in hardware_lower:
            return "esp32"
        
        # CP210x chips are commonly used in ESP32 boards
        if "10c4:ea60" in hardware_lower:  # CP2102/CP2104
            return "esp32"
        
        # CH340 is very common in ESP8266 boards, but also used in ESP32
        # Default to ESP8266 for CH340 unless other indicators suggest ESP32
        if "1a86:7523" in hardware_lower:  # CH340/CH341
            return "esp8266"
        
        # FTDI can be used for either, default to ESP32 as it's more common in newer boards
        if "0403:" in hardware_lower:  # FTDI chips
            return "esp32"
        
        # Default fallback - could be made configurable
        return "esp8266"

    def flash_device(self, device: Device) -> bool:
        """
        Flash a single ESP8266/ESP32 device with WLED firmware.
        
        Args:
            device: Device object to flash
            
        Returns:
            True if flash was successful, False otherwise
        """
        port = device.port
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Determine which PlatformIO environment to use
        if device.device_type == "esp32":
            environment = "esp32dev"
        else:  # default to esp8266 for unknown devices too
            environment = "esp8266_2m"
        
        print(f"🔄 [{timestamp}] Starting flash for {device.device_type.upper()} device: {port}")
        print(f"   Environment: {environment}")
        print(f"   Hardware: {device.hardware_id}")
        print(f"   Description: {device.description}")
        
        try:
            # Run the PlatformIO upload command
            result = subprocess.run([
                "pio", "run", 
                "-e", environment, 
                "--target", "upload", 
                "--upload-port", port
            ], 
            capture_output=True, 
            text=True, 
            timeout=300  # 5 minute timeout
            )
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if result.returncode == 0:
                print(f"✅ [{timestamp}] SUCCESS: {port} flashed successfully!")
                print(f"🔌 Device on {port} can now be disconnected")
                print()
                return True
            else:
                print(f"❌ [{timestamp}] FAILED: {port} flash failed")
                print(f"   Error: {result.stderr}")
                print()
                return False
                
        except subprocess.TimeoutExpired:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"⏰ [{timestamp}] TIMEOUT: {port} flash timed out (5 minutes)")
            print()
            return False
            
        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"❌ [{timestamp}] ERROR: {port} flash error: {e}")
            print()
            return False

    def flash_device_thread(self, device: Device):
        """
        Thread wrapper for flashing a device.
        
        Args:
            device: Device object to flash
        """
        try:
            with self.flash_lock:
                self.total_attempts += 1
            
            success = self.flash_device(device)
            
            with self.flash_lock:
                if success:
                    self.successful_flashes += 1
                else:
                    self.failed_flashes += 1
                    
                # Remove from active flashes
                if device.port in self.active_flashes:
                    del self.active_flashes[device.port]
                    
                self._print_stats()
                
        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"❌ [{timestamp}] Thread error for {device.port}: {e}")
            
            with self.flash_lock:
                self.failed_flashes += 1
                if device.port in self.active_flashes:
                    del self.active_flashes[device.port]

    def _print_stats(self):
        """Print current statistics."""
        print(f"📊 Stats: {self.successful_flashes} successful, {self.failed_flashes} failed, {len(self.active_flashes)} active")
        print()

    def start_flash_for_device(self, device: Device):
        """
        Start flashing a device in a separate thread.
        
        Args:
            device: Device object to flash
        """
        with self.flash_lock:
            if device.port in self.active_flashes:
                return  # Already flashing this device
                
            # Start flash thread
            flash_thread = threading.Thread(
                target=self.flash_device_thread,
                args=(device,),
                daemon=True
            )
            
            self.active_flashes[device.port] = flash_thread
            self.processed_devices.add(device.port)
            
        flash_thread.start()

    def scan_and_flash(self):
        """
        Main scanning loop that looks for new devices and starts flashing them.
        """
        while self.running:
            try:
                # Get currently connected devices
                devices = self.get_connected_devices()
                
                # Find new devices (not yet processed or currently being flashed)
                new_devices = []
                for device in devices:
                    if device.port not in self.processed_devices:
                        new_devices.append(device)
                
                # Start flashing new devices
                for device in new_devices:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"🔍 [{timestamp}] New {device.device_type.upper()} device detected: {device.port}")
                    self.start_flash_for_device(device)
                
                # Clean up finished threads
                with self.flash_lock:
                    finished_ports = []
                    for port, thread in self.active_flashes.items():
                        if not thread.is_alive():
                            finished_ports.append(port)
                    
                    for port in finished_ports:
                        del self.active_flashes[port]
                
                # Wait before next scan
                time.sleep(self.scan_interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping auto-flasher...")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(self.scan_interval)

    def run(self):
        """
        Start the auto-flasher.
        """
        self.running = True
        
        try:
            # Check if PlatformIO is available
            subprocess.run(["pio", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ PlatformIO not found. Please install PlatformIO first:")
            print("   pip install platformio")
            sys.exit(1)
        
        try:
            self.scan_and_flash()
        finally:
            self.running = False
            
            # Wait for active flashes to complete
            print("⏳ Waiting for active flashes to complete...")
            with self.flash_lock:
                active_threads = list(self.active_flashes.values())
            
            for thread in active_threads:
                thread.join(timeout=10)  # Wait up to 10 seconds
            
            print("👋 Auto-flasher stopped")
            self._print_stats()


def main():
    """Main entry point."""
    flasher = WLEDAutoFlasher(scan_interval=2.0)
    flasher.run()


if __name__ == "__main__":
    main()