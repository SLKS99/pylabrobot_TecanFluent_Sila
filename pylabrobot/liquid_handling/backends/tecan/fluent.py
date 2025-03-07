"""Backend implementation for controlling Tecan Fluent using the official Tecan Fluent SiLA2 connector."""

import time
import logging
import asyncio
from typing import Any, Dict, List, Optional, Union

# Import SiLA2 connector with detailed error handling
HAS_TECAN_SILA = False
try:
    from tecan.fluent import Fluent as TecanFluent
    from tecan.fluent import DiTi, Labware, Liquid, Position
    from tecan.fluent import SiLA2Error, ConnectionError, AuthenticationError
    HAS_TECAN_SILA = True
    print("Successfully imported tecan.fluent module.")
except ImportError as e:
    import warnings
    import sys
    warnings.warn(
        f"\nTecan Fluent SiLA2 connector not found: {e}"
        "\nTo use this backend:"
        "\n1. Contact Tecan support for access to their SiLA2 connector package"
        "\n2. Install the package using pip with their repository URL"
        f"\nPython path: {sys.path}"
    )
except ImportError:
    HAS_TECAN_SILA = False

# PyLabRobot imports
from pylabrobot.liquid_handling.backends.backend import LiquidHandlerBackend
from pylabrobot.liquid_handling.standard import (
    Drop,
    DropTipRack,
    MultiHeadAspirationContainer,
    MultiHeadAspirationPlate,
    MultiHeadDispenseContainer,
    MultiHeadDispensePlate,
    Pickup,
    PickupTipRack,
    ResourceDrop,
    ResourceMove,
    ResourcePickup,
    SingleChannelAspiration,
    SingleChannelDispense,
)
from pylabrobot.resources import Resource, Coordinate, Liquid

class Fluent(LiquidHandlerBackend):
    def __init__(
        self,
        num_channels: int,
        host: str = "127.0.0.1",
        port: int = 50052,
        insecure: bool = True,
        username: str = None,
        password: str = None,
        discovery_time: int = 10,
        method_name: str = "pylabrobot",
        operation_timeout: int = 30,
        connection_timeout: int = 10
    ):
        """Create a new Tecan Fluent backend.

        Args:
            num_channels: The number of channels on the liquid handler.
            host: The hostname where the Tecan Fluent SiLA server is running.
            port: The port where the Tecan Fluent SiLA server is running.
            insecure: Whether to use insecure connection (no SSL).
            username: Username for UMS authentication (optional).
            password: Password for UMS authentication (optional).
            discovery_time: Time in seconds to wait for server discovery (optional).
            method_name: Name of the Fluent method to use (must be loaded in FluentControl).
            operation_timeout: Timeout for operation in seconds (optional).
            connection_timeout: Timeout for connection in seconds (optional).
        """
        if not HAS_TECAN_SILA:
            raise RuntimeError(
                "The Tecan Fluent backend requires the Tecan Fluent SiLA2 connector. "
                "Please install it from: https://gitlab.com/tecan/fluent-sila2-connector"
            )

        # Validate num_channels
        if not isinstance(num_channels, int) or num_channels <= 0:
            raise ValueError("num_channels must be a positive integer")

        # Validate host and port
        if not isinstance(host, str):
            raise TypeError("host must be a string")
        if not isinstance(port, int) or port <= 0 or port > 65535:
            raise ValueError("port must be a valid port number (1-65535)")

        super().__init__()
        self._num_channels = num_channels
        self.host = host
        self.port = port
        self.insecure = insecure
        self.username = username
        self.password = password
        self.discovery_time = discovery_time
        self.method_name = method_name
        self.operation_timeout = operation_timeout
        self.connection_timeout = connection_timeout
        self.fluent = None

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("FluentBackend")
        self.logger.info("Tecan Fluent backend initialized")

    # ... rest of the class implementation remains the same ...