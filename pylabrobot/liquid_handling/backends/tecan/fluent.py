"""Backend implementation for controlling Tecan Fluent using the official Tecan Fluent SiLA2 connector."""

import logging
from typing import Any, Dict, List, Optional, Union, cast

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
        username: Optional[str] = None,
        password: Optional[str] = None,
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
            username: Username for UMS authentication (optional).
            password: Password for UMS authentication (optional).
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
        self.username = username
        self.password = password
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
        """Set up the connection to the Fluent server."""
        try:
            self.logger.info(f"Connecting to Fluent server at {self.host}:{self.port}")
            self.fluent = TecanFluent(
                self.host,
                self.port,
                insecure=self.insecure,
                username=self.username,
                password=self.password
            )
            self.fluent.start_fluent()
            self.logger.info("Successfully connected to Fluent server")
        except Exception as e:
            self.logger.error(f"Failed to connect to Fluent server: {e}")
            raise

    async def stop(self) -> None:
        """Stop the connection to the Fluent server."""
        if self.fluent:
            try:
                self.fluent.stop()
                self.logger.info("Successfully stopped Fluent server connection")
            except Exception as e:
                self.logger.error(f"Error stopping Fluent server: {e}")
                raise

    # SiLA Worklist and Method Management Methods

    async def get_available_methods(self) -> List[str]:
        """Get a list of available methods from the Fluent server.

        Returns:
            List[str]: List of available method names.
        """
        if self.simulation_mode:
            return ["simulation_method"]

        try:
            methods = await self.fluent.get_available_methods()
            self.logger.info(f"Retrieved {len(methods)} available methods")
            return methods
        except Exception as e:
            self.logger.error(f"Failed to get available methods: {e}")
            raise

    async def get_method_parameters(self, method_name: str) -> Dict[str, Any]:
        """Get the parameters for a specific method.

        Args:
            method_name: Name of the method to get parameters for.

        Returns:
            Dict[str, Any]: Dictionary of parameter names and their types/values.
        """
        if self.simulation_mode:
            return {"param1": "value1", "param2": "value2"}

        try:
            params = await self.fluent.get_method_parameters(method_name)
            self.logger.info(f"Retrieved parameters for method: {method_name}")
            return params
        except Exception as e:
            self.logger.error(f"Failed to get method parameters: {e}")
            raise

    async def add_to_worklist(self, method_name: str, parameters: Dict[str, Any]) -> bool:
        """Add a method to the worklist.

        Args:
            method_name: Name of the method to add.
            parameters: Dictionary of parameters for the method.

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.simulation_mode:
            self.logger.info(f"Simulation: Added {method_name} to worklist")
            return True

        try:
            await self.fluent.add_to_worklist(method_name, parameters)
            self.logger.info(f"Added {method_name} to worklist")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add method to worklist: {e}")
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
            List[Dict[str, Any]]: List of methods in the worklist with their parameters.
        """
        if self.simulation_mode:
            return []

        try:
            worklist = await self.fluent.get_worklist()
            self.logger.info("Retrieved current worklist")
            return worklist
        except Exception as e:
            self.logger.error(f"Failed to get worklist: {e}")
            raise

    async def run_worklist(self) -> bool:
        """Run the current worklist.

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.simulation_mode:
            self.logger.info("Simulation: Running worklist")
            return True

        try:
            await self.fluent.run_worklist()
            self.logger.info("Started worklist execution")
            return True
        except Exception as e:
            self.logger.error(f"Failed to run worklist: {e}")
            return False

    async def get_worklist_status(self) -> str:
        """Get the current status of the worklist.

        Returns:
            str: Current status of the worklist.
        """
        if self.simulation_mode:
            return "Completed"

        try:
            status = await self.fluent.get_worklist_status()
            self.logger.info(f"Worklist status: {status}")
            return status
        except Exception as e:
            self.logger.error(f"Failed to get worklist status: {e}")
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

    # Core Liquid Handling Methods

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
            # Convert tip spot to SiLA position
            position = self._resource_to_position(tip_spot)
            await self.fluent.pick_up_tips(position)
            self.logger.info(f"Successfully picked up tips from {tip_spot}")
        except Exception as e:
            self.logger.error(f"Failed to pick up tips: {e}")
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
            # Convert tip spot to SiLA position
            position = self._resource_to_position(tip_spot)
            await self.fluent.drop_tips(position)
            self.logger.info(f"Successfully dropped tips to {tip_spot}")
        except Exception as e:
            self.logger.error(f"Failed to drop tips: {e}")
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
            # Convert resource to SiLA position and liquid
            position = self._resource_to_position(resource)
            liquid = self._resource_to_liquid(resource)

            await self.fluent.aspirate(
                position=position,
                volume=volume,
                flow_rate=flow_rate,
                liquid_height=liquid_height,
                blow_out=blow_out,
                liquid=liquid
            )
            self.logger.info(f"Successfully aspirated {volume}µL from {resource}")
        except Exception as e:
            self.logger.error(f"Failed to aspirate: {e}")
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
            # Convert resource to SiLA position and liquid
            position = self._resource_to_position(resource)
            liquid = self._resource_to_liquid(resource)

            await self.fluent.dispense(
                position=position,
                volume=volume,
                flow_rate=flow_rate,
                liquid_height=liquid_height,
                blow_out=blow_out,
                liquid=liquid
            )
            self.logger.info(f"Successfully dispensed {volume}µL to {resource}")
        except Exception as e:
            self.logger.error(f"Failed to dispense: {e}")
            raise

    def _resource_to_position(self, resource: Resource) -> Position:
        """Convert a PyLabRobot resource to a SiLA Position.

        Args:
            resource: The resource to convert.

        Returns:
            Position: The SiLA Position object.

        Raises:
            ValueError: If the resource does not have a location.
        """
        if not hasattr(resource, "location"):
            raise ValueError(f"Resource {resource} does not have a location")

        location = resource.location
        return Position(
            x=location.x,
            y=location.y,
            z=location.z
        )

    def _resource_to_liquid(self, resource: Resource) -> Liquid:
        """Convert a PyLabRobot resource's liquid to a SiLA Liquid.

        Args:
            resource: The resource to convert.

        Returns:
            Liquid: The SiLA Liquid object.
        """
        if not hasattr(resource, "liquid"):
            return Liquid.WATER  # Default to water if no liquid specified

        liquid = resource.liquid
        # Map PyLabRobot liquid types to SiLA liquid types
        liquid_map = {
            "water": Liquid.WATER,
            "dmso": Liquid.DMSO,
            "ethanol": Liquid.ETHANOL,
            # Add more mappings as needed
        }
        return liquid_map.get(liquid.name.lower(), Liquid.WATER)