from typing import Any, Dict, List, Optional
from pylabrobot.liquid_handling.backends.backend import LiquidHandlerBackend
from pylabrobot.resources import Resource

try:
    from tecan.fluent.sila2 import FluentControl  # type: ignore
    HAS_TECAN_SILA = True
except ImportError:
    HAS_TECAN_SILA = False

class TecanSiLABackend(LiquidHandlerBackend):
    """A backend that uses Tecan's SiLA 2 connector to control a Tecan Fluent liquid handler."""

    def __init__(
        self,
        num_channels: int,
        host: str = "localhost",
        port: int = 50051,
        method_name: str = None,  # Name of the FluentControl method to execute
    ):
        """Create a new TecanSiLA backend.

        Args:
            num_channels: The number of channels on the liquid handler.
            host: The hostname where the Tecan SiLA server is running.
            port: The port where the Tecan SiLA server is running.
            method_name: Name of the FluentControl method to execute (optional).
        """

        if not HAS_TECAN_SILA:
            raise RuntimeError(
                "The TecanSiLA backend requires the tecan-fluent-sila2-connector package. "
                "Please install it from the Tecan Fluent SiLA2 connector distribution."
            )

        super().__init__()
        self._num_channels = num_channels
        self.host = host
        self.port = port
        self.method_name = method_name
        self.fluent_control = None

    @property
    def num_channels(self) -> int:
        return self._num_channels

    async def setup(self):
        """Set up the connection to the Tecan SiLA server and initialize FluentControl."""
        await super().setup()
        # Connect to the Tecan SiLA server
        self.fluent_control = FluentControl(
            host=self.host,
            port=self.port
        )
        await self.fluent_control.connect()

        # Initialize FluentControl if a method is specified
        if self.method_name:
            await self.load_method(self.method_name)

    async def stop(self):
        """Stop the connection to the SiLA server and cleanup FluentControl."""
        if self.fluent_control:
            await self.fluent_control.disconnect()
            self.fluent_control = None

    async def load_method(self, method_name: str):
        """Load a FluentControl method."""
        await self.fluent_control.load_method(method_name)

    async def execute_method(self, method_id: str = None):
        """Execute a loaded FluentControl method."""
        if method_id is None:
            method_id = await self.fluent_control.get_current_method_id()
        if method_id is None:
            raise RuntimeError("No method loaded. Call load_method first.")

        await self.fluent_control.execute_method(method_id)

        # Wait for method completion
        while True:
            status = await self.fluent_control.get_method_status(method_id)
            if status.state in ["Completed", "Error", "Aborted"]:
                if status.state != "Completed":
                    raise RuntimeError(f"Method execution failed: {status.state}")
                break
            await asyncio.sleep(1)

    def serialize(self) -> dict:
        return {
            **super().serialize(),
            "num_channels": self.num_channels,
            "host": self.host,
            "port": self.port,
            "method_name": self.method_name
        }

    async def pick_up_tips(self, ops: List["Pickup"], **backend_kwargs):
        """Pick up tips using FluentControl."""
        if not self.fluent_control:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to FluentControl commands
        tip_positions = []
        for op in ops:
            for tip in op.tips:
                pos = tip.get_absolute_location()
                tip_positions.append({
                    "carrier": tip.parent.name,  # Assuming this matches FluentControl carrier name
                    "position": f"{pos.x:.1f},{pos.y:.1f},{pos.z:.1f}",
                    "site": tip.get_name()  # e.g., "A1"
                })

        # Create and execute a tip pickup method
        method_name = "TipPickup"
        await self.fluent_control.create_tip_pickup_method(
            method_name=method_name,
            positions=tip_positions
        )
        await self.load_method(method_name)
        await self.execute_method()

    async def drop_tips(self, ops: List["Drop"], **backend_kwargs):
        """Drop tips using FluentControl."""
        if not self.fluent_control:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to FluentControl commands
        tip_positions = []
        for op in ops:
            for tip in op.tips:
                pos = tip.get_absolute_location()
                tip_positions.append({
                    "carrier": tip.parent.name,
                    "position": f"{pos.x:.1f},{pos.y:.1f},{pos.z:.1f}",
                    "site": tip.get_name()
                })

        # Create and execute a tip drop method
        method_name = "TipDrop"
        await self.fluent_control.create_tip_drop_method(
            method_name=method_name,
            positions=tip_positions
        )
        await self.load_method(method_name)
        await self.execute_method()

    async def aspirate(self, ops: List["SingleChannelAspiration"], **backend_kwargs):
        """Aspirate liquid using FluentControl."""
        if not self.fluent_control:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to FluentControl commands
        aspirate_positions = []
        for op in ops:
            pos = op.resource.get_absolute_location()
            aspirate_positions.append({
                "carrier": op.resource.parent.name,
                "position": f"{pos.x:.1f},{pos.y:.1f},{pos.z:.1f}",
                "site": op.resource.get_name(),
                "volume": op.volume,
                "liquid_class": backend_kwargs.get("liquid_class", "Water"),  # Default to water
                "liquid_height": op.liquid_height,
                "flow_rate": op.flow_rate
            })

        # Create and execute an aspiration method
        method_name = "Aspiration"
        await self.fluent_control.create_aspiration_method(
            method_name=method_name,
            positions=aspirate_positions
        )
        await self.load_method(method_name)
        await self.execute_method()

    async def dispense(self, ops: List["SingleChannelDispense"], **backend_kwargs):
        """Dispense liquid using FluentControl."""
        if not self.fluent_control:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to FluentControl commands
        dispense_positions = []
        for op in ops:
            pos = op.resource.get_absolute_location()
            dispense_positions.append({
                "carrier": op.resource.parent.name,
                "position": f"{pos.x:.1f},{pos.y:.1f},{pos.z:.1f}",
                "site": op.resource.get_name(),
                "volume": op.volume,
                "liquid_class": backend_kwargs.get("liquid_class", "Water"),
                "liquid_height": op.liquid_height,
                "flow_rate": op.flow_rate
            })

        # Create and execute a dispense method
        method_name = "Dispense"
        await self.fluent_control.create_dispense_method(
            method_name=method_name,
            positions=dispense_positions
        )
        await self.load_method(method_name)
        await self.execute_method()

    async def pick_up_resource(self, ops: List["ResourcePickup"], **backend_kwargs):
        """Pick up a resource using FluentControl."""
        if not self.fluent_control:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to FluentControl commands
        resource_positions = []
        for op in ops:
            pos = op.resource.get_absolute_location()
            resource_positions.append({
                "carrier": op.resource.parent.name,
                "position": f"{pos.x:.1f},{pos.y:.1f},{pos.z:.1f}",
                "site": op.resource.get_name()
            })

        # Create and execute a resource pickup method
        method_name = "ResourcePickup"
        await self.fluent_control.create_resource_pickup_method(
            method_name=method_name,
            positions=resource_positions
        )
        await self.load_method(method_name)
        await self.execute_method()

    async def move_picked_up_resource(self, ops: List["ResourceMove"], **backend_kwargs):
        """Move a picked up resource using FluentControl."""
        if not self.fluent_control:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to FluentControl commands
        resource_positions = []
        for op in ops:
            pos = op.resource.get_absolute_location()
            resource_positions.append({
                "carrier": op.resource.parent.name,
                "position": f"{pos.x:.1f},{pos.y:.1f},{pos.z:.1f}",
                "site": op.resource.get_name()
            })

        # Create and execute a resource move method
        method_name = "ResourceMove"
        await self.fluent_control.create_resource_move_method(
            method_name=method_name,
            positions=resource_positions
        )
        await self.load_method(method_name)
        await self.execute_method()

    async def drop_resource(self, ops: List["ResourceDrop"], **backend_kwargs):
        """Drop a resource using FluentControl."""
        if not self.fluent_control:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to FluentControl commands
        resource_positions = []
        for op in ops:
            pos = op.resource.get_absolute_location()
            resource_positions.append({
                "carrier": op.resource.parent.name,
                "position": f"{pos.x:.1f},{pos.y:.1f},{pos.z:.1f}",
                "site": op.resource.get_name()
            })

        # Create and execute a resource drop method
        method_name = "ResourceDrop"
        await self.fluent_control.create_resource_drop_method(
            method_name=method_name,
            positions=resource_positions
        )
        await self.load_method(method_name)
        await self.execute_method()