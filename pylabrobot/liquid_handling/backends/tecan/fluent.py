"""Backend implementation for controlling Tecan Fluent using the official Tecan Fluent SiLA2 connector.

This backend assumes:
1. The Tecan Fluent SiLA server is already running (started separately)
2. The tecan.fluent package is installed in the virtual environment
3. The server is accessible at the specified host and port
"""

import logging
import sys
from typing import Any, Dict, List, Optional, Union, cast
import asyncio
import warnings

# Import SiLA2 connector with detailed error handling
HAS_TECAN_SILA = False
try:
    from tecan import Fluent as TecanFluent
    HAS_TECAN_SILA = True
except ImportError as e:
    warnings.warn(
        f"\nTecan Fluent SiLA2 connector not found: {e}"
        "\nTo use this backend:"
        "\n1. Contact Tecan support for access to their SiLA2 connector package"
        "\n2. Install the package using pip with their repository URL"
        f"\nPython path: {sys.path}"
    )

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
    """Backend for controlling Tecan Fluent liquid handlers using the SiLA2 connector."""

    def __init__(
        self,
        num_channels: int,
        host: str = "127.0.0.1",
        port: int = 50052,
        insecure: bool = True,
        discovery_time: int = 10,
        method_name: str = "pylabrobot",
        operation_timeout: int = 30,
        connection_timeout: int = 10,
        simulation_mode: bool = False
    ) -> None:
        """Create a new Tecan Fluent backend.

        Args:
            num_channels: The number of channels on the liquid handler.
            host: The hostname where the Tecan Fluent SiLA server is running.
            port: The port where the Tecan Fluent SiLA server is running.
            insecure: Whether to use insecure connection (no SSL).
            discovery_time: Time in seconds to wait for server discovery (optional).
            method_name: Name of the Fluent method to use (must be loaded in FluentControl).
            operation_timeout: Timeout for operation in seconds (optional).
            connection_timeout: Timeout for connection in seconds (optional).
            simulation_mode: Whether to run in simulation mode (optional).
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
        self.discovery_time = discovery_time
        self.method_name = method_name
        self.operation_timeout = operation_timeout
        self.connection_timeout = connection_timeout
        self.simulation_mode = simulation_mode
        self.fluent: Optional[TecanFluent] = None

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("FluentBackend")
        self.logger.info("Tecan Fluent backend initialized")

    @property
    def num_channels(self) -> int:
        """Get the number of channels on the liquid handler."""
        return self._num_channels

    async def setup(self) -> None:
        """Set up the connection to the Fluent server.

        This method:
        1. Creates a connection to the existing SiLA server using the Tecan connector
        2. Starts FluentControl and waits for it to be ready
        3. Validates the connection is working

        Raises:
            ConnectionError: If the server is not running or not accessible
            RuntimeError: If FluentControl is not properly initialized
        """
        if TecanFluent is None:
            raise RuntimeError(
                "Tecan Fluent SiLA2 connector not found. "
                "Please contact Tecan support for access to their SiLA2 connector package."
            )
        try:
            self.logger.info(f"Connecting to Fluent server at {self.host}:{self.port}")

            # Create the SiLA client (does not start a server)
            self.fluent = TecanFluent(
                self.host,
                self.port,
                insecure=self.insecure
            )

            # Start FluentControl if needed
            self.logger.info("Starting FluentControl...")
            try:
                self.fluent.start_fluent()
                self.logger.info("FluentControl start command sent")
            except Exception as e:
                self.logger.warning(f"Could not start FluentControl (it may already be running): {e}")

            # Subscribe to state changes
            def state_changed_callback(state):
                self.logger.info(f"FluentControl state changed to: {state}")
            self.fluent.subscribe_state(state_changed_callback)

            # Check current state
            current_state = self.fluent.state
            self.logger.info(f"Current FluentControl state: {current_state}")

            # Try to get available methods to verify connection
            try:
                self.logger.info("Getting available methods...")
                methods = self.fluent.get_all_runnable_methods()
                self.logger.info(f"Available methods: {methods}")
                if not methods:
                    self.logger.warning("No methods available in FluentControl")
            except Exception as e:
                self.logger.error(
                    "Could not get available methods. "
                    "Please ensure a method is loaded in FluentControl."
                )
                raise RuntimeError(
                    "Failed to get available methods. "
                    "Please ensure FluentControl has a method loaded."
                ) from e

            self.logger.info("Successfully connected to Fluent server")

        except Exception as e:
            self.logger.error(f"Failed to connect to Fluent server: {e}")
            raise

    async def stop(self) -> None:
        """Stop the connection to the Fluent server."""
        if self.fluent:
            try:
                # Don't stop the server, just clean up our connection
                self.fluent = None
                self.logger.info("Successfully disconnected from Fluent server")
            except Exception as e:
                self.logger.error(f"Error disconnecting from Fluent server: {e}")
                raise

    # SiLA Worklist and Method Management Methods

    def get_available_methods(self) -> List[str]:
        """Get a list of available methods from the Fluent server.

        Returns:
            List[str]: List of available method names.
        """
        if not self.fluent:
            raise RuntimeError("Fluent backend not initialized. Call setup() first.")

        if self.simulation_mode:
            return ["simulation_method"]

        try:
            # get_all_runnable_methods is synchronous
            methods = self.fluent.get_all_runnable_methods()
            self.logger.info(f"Retrieved {len(methods)} available methods")
            return methods
        except Exception as e:
            self.logger.error(f"Failed to get available methods: {e}")
            raise

    async def get_available_labware(self) -> List[str]:
        """Get a list of available labware from FluentControl.

        Returns:
            List[str]: List of labware names that are configured in FluentControl.
        """
        try:
            # Try to get labware through variables first
            variables = self.fluent.get_variable_names()
            labware = [v for v in variables if v.startswith("labware_")]
            if labware:
                return labware

            # If no labware variables, try to get through method parameters
            methods = await self.get_available_methods()
            if methods:
                try:
                    params = await self.get_method_parameters(methods[0])
                    labware_params = [p for p in params if "labware" in p.lower()]
                    if labware_params:
                        return labware_params
                except Exception:
                    pass

            self.logger.warning("No labware found in FluentControl")
            return []
        except Exception as e:
            self.logger.error(f"Error getting available labware: {e}")
            raise

    async def get_method_parameters(self, method_name: str) -> Dict[str, Any]:
        """Get parameters for a specific method.

        Args:
            method_name: Name of the method to get parameters for.

        Returns:
            Dict[str, Any]: Dictionary of parameter names and their values.
        """
        try:
            # Try to get method parameters through SiLA2 connector
            if hasattr(self.fluent, 'get_method_parameters'):
                params = self.fluent.get_method_parameters(method_name)
                self.logger.info(f"Got parameters for method {method_name}")
                return params

            # If method doesn't exist, try to get through variables
            variables = self.fluent.get_variable_names()
            method_vars = [v for v in variables if v.startswith(f"{method_name}_")]
            if method_vars:
                return {v: self.fluent.get_variable_value(v) for v in method_vars}

            self.logger.warning(f"No parameters found for method {method_name}")
            return {}
        except Exception as e:
            self.logger.error(f"Error getting method parameters: {e}")
            raise

    async def add_to_worklist(self, method_name: str, parameters: Dict[str, Any]) -> bool:
        """Add a method to the worklist.

        Args:
            method_name: Name of the method to add.
            parameters: Dictionary of parameters for the method.

        Returns:
            bool: True if successful.
        """
        try:
            # Prepare the method first
            self.fluent.prepare_method(method_name)
            self.logger.info(f"Prepared method {method_name}")

            # Set any parameters
            for name, value in parameters.items():
                if hasattr(self.fluent, 'set_variable_value'):
                    self.fluent.set_variable_value(name, value)

            return True
        except Exception as e:
            self.logger.error(f"Error adding method to worklist: {e}")
            return False

    async def clear_worklist(self) -> bool:
        """Clear the current worklist.

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.simulation_mode:
            self.logger.info("Simulation: Cleared worklist")
            return True

        try:
            await self.fluent.clear_worklist()
            self.logger.info("Cleared worklist")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear worklist: {e}")
            return False

    async def get_worklist(self) -> List[Dict[str, Any]]:
        """Get the current worklist.

        Returns:
            List[Dict[str, Any]]: List of methods in the worklist.
        """
        try:
            if hasattr(self.fluent, 'get_worklist'):
                worklist = self.fluent.get_worklist()
                self.logger.info("Got current worklist")
                return worklist
            return []
        except Exception as e:
            self.logger.error(f"Error getting worklist: {e}")
            raise

    async def run_worklist(self) -> bool:
        """Run the current worklist.

        Returns:
            bool: True if successful.
        """
        try:
            if hasattr(self.fluent, 'run_method'):
                self.fluent.run_method()
                self.logger.info("Started worklist execution")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error running worklist: {e}")
            return False

    async def get_worklist_status(self) -> str:
        """Get the current status of the worklist.

        Returns:
            str: Current status.
        """
        try:
            return self.fluent.state
        except Exception as e:
            self.logger.error(f"Error getting worklist status: {e}")
            raise

    async def pause_worklist(self) -> bool:
        """Pause the current worklist execution.

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.simulation_mode:
            self.logger.info("Simulation: Paused worklist")
            return True

        try:
            await self.fluent.pause_worklist()
            self.logger.info("Paused worklist execution")
            return True
        except Exception as e:
            self.logger.error(f"Failed to pause worklist: {e}")
            return False

    async def resume_worklist(self) -> bool:
        """Resume the paused worklist execution.

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.simulation_mode:
            self.logger.info("Simulation: Resumed worklist")
            return True

        try:
            await self.fluent.resume_worklist()
            self.logger.info("Resumed worklist execution")
            return True
        except Exception as e:
            self.logger.error(f"Failed to resume worklist: {e}")
            return False

    async def stop_worklist(self) -> bool:
        """Stop the current worklist execution.

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.simulation_mode:
            self.logger.info("Simulation: Stopped worklist")
            return True

        try:
            await self.fluent.stop_worklist()
            self.logger.info("Stopped worklist execution")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop worklist: {e}")
            return False

    # Core Liquid Handling Methods - Using Worklist Approach

    async def pick_up_tips(self, tip_spot: Resource, **backend_kwargs: Any) -> None:
        """Pick up tips from a tip spot.

        Args:
            tip_spot: The resource containing the tips to pick up.
            **backend_kwargs: Additional backend-specific arguments.
        """
        if self.simulation_mode:
            self.logger.info(f"Simulation: Picking up tips from {tip_spot}")
            return

        try:
            # Add tip pickup to worklist
            parameters = {
                "tip_spot": tip_spot.name,  # Use resource name as identifier
                "num_channels": self.num_channels,
                **backend_kwargs
            }
            await self.add_to_worklist("pick_up_tips", parameters)
            self.logger.info(f"Added tip pickup from {tip_spot} to worklist")
        except Exception as e:
            self.logger.error(f"Failed to add tip pickup to worklist: {e}")
            raise

    async def drop_tips(self, tip_spot: Resource, **backend_kwargs: Any) -> None:
        """Drop tips to a tip spot.

        Args:
            tip_spot: The resource to drop tips to.
            **backend_kwargs: Additional backend-specific arguments.
        """
        if self.simulation_mode:
            self.logger.info(f"Simulation: Dropping tips to {tip_spot}")
            return

        try:
            # Add tip drop to worklist
            parameters = {
                "tip_spot": tip_spot.name,  # Use resource name as identifier
                "num_channels": self.num_channels,
                **backend_kwargs
            }
            await self.add_to_worklist("drop_tips", parameters)
            self.logger.info(f"Added tip drop to {tip_spot} to worklist")
        except Exception as e:
            self.logger.error(f"Failed to add tip drop to worklist: {e}")
            raise

    async def aspirate(
        self,
        resource: Resource,
        volume: float,
        flow_rate: float = 100,
        liquid_height: float = 1.0,
        blow_out: bool = True,
        **backend_kwargs: Any
    ) -> None:
        """Aspirate liquid from a resource.

        Args:
            resource: The resource to aspirate from.
            volume: Volume to aspirate in µL.
            flow_rate: Flow rate in µL/s.
            liquid_height: Height of liquid from bottom in mm.
            blow_out: Whether to blow out after aspiration.
            **backend_kwargs: Additional backend-specific arguments.
        """
        if self.simulation_mode:
            self.logger.info(f"Simulation: Aspirating {volume}µL from {resource}")
            return

        try:
            # Add aspiration to worklist
            parameters = {
                "resource": resource.name,  # Use resource name as identifier
                "volume": volume,
                "flow_rate": flow_rate,
                "liquid_height": liquid_height,
                "blow_out": blow_out,
                "num_channels": self.num_channels,
                **backend_kwargs
            }
            await self.add_to_worklist("aspirate", parameters)
            self.logger.info(f"Added aspiration from {resource} to worklist")
        except Exception as e:
            self.logger.error(f"Failed to add aspiration to worklist: {e}")
            raise

    async def dispense(
        self,
        resource: Resource,
        volume: float,
        flow_rate: float = 100,
        liquid_height: float = 1.0,
        blow_out: bool = True,
        **backend_kwargs: Any
    ) -> None:
        """Dispense liquid to a resource.

        Args:
            resource: The resource to dispense to.
            volume: Volume to dispense in µL.
            flow_rate: Flow rate in µL/s.
            liquid_height: Height of liquid from bottom in mm.
            blow_out: Whether to blow out after dispensing.
            **backend_kwargs: Additional backend-specific arguments.
        """
        if self.simulation_mode:
            self.logger.info(f"Simulation: Dispensing {volume}µL to {resource}")
            return

        try:
            # Add dispense to worklist
            parameters = {
                "resource": resource.name,  # Use resource name as identifier
                "volume": volume,
                "flow_rate": flow_rate,
                "liquid_height": liquid_height,
                "blow_out": blow_out,
                "num_channels": self.num_channels,
                **backend_kwargs
            }
            await self.add_to_worklist("dispense", parameters)
            self.logger.info(f"Added dispense to {resource} to worklist")
        except Exception as e:
            self.logger.error(f"Failed to add dispense to worklist: {e}")
            raise

    # Required abstract methods from LiquidHandlerBackend
    async def aspirate96(self, resource: Resource, volume: float, flow_rate: float = 100.0, liquid_height: float = 1.0, blow_out: bool = True) -> None:
        """Not implemented - required by abstract class."""
        pass

    async def dispense96(self, resource: Resource, volume: float, flow_rate: float = 100.0, liquid_height: float = 1.0, blow_out: bool = True) -> None:
        """Not implemented - required by abstract class."""
        pass

    async def pick_up_tips96(self, resource: Resource) -> None:
        """Not implemented - required by abstract class."""
        pass

    async def drop_tips96(self, resource: Resource) -> None:
        """Not implemented - required by abstract class."""
        pass

    async def pick_up_resource(self, resource: Resource) -> None:
        """Not implemented - required by abstract class."""
        pass

    async def drop_resource(self, resource: Resource) -> None:
        """Not implemented - required by abstract class."""
        pass

    async def move_picked_up_resource(self, resource: Resource, to_coordinate: Coordinate) -> None:
        """Not implemented - required by abstract class."""
        pass