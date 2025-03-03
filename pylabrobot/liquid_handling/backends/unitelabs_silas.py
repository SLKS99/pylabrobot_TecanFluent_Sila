from typing import Any, Dict, List, Optional, cast
from pylabrobot.liquid_handling.backends.backend import LiquidHandlerBackend
from pylabrobot.resources import Resource

try:
    import unitelabs.silas  # type: ignore
    HAS_SILAS = True
except ImportError:
    HAS_SILAS = False

class UnitelabsSilasBackend(LiquidHandlerBackend):
    """A backend that uses UnitelabsSilas to control a Tecan Fluent liquid handler."""

    def __init__(
        self,
        num_channels: int,
        host: str = "localhost",
        port: int = 50051,
    ):
        """Create a new UnitelabsSilas backend.

        Args:
            num_channels: The number of channels on the liquid handler.
            host: The hostname where the SiLA server is running.
            port: The port where the SiLA server is running.
        """

        if not HAS_SILAS:
            raise RuntimeError("The UnitelabsSilas backend requires the unitelabs.silas package.")

        super().__init__()
        self._num_channels = num_channels
        self.host = host
        self.port = port
        self.client = None

    @property
    def num_channels(self) -> int:
        return self._num_channels

    async def setup(self):
        """Set up the connection to the SiLA server."""
        await super().setup()
        self.client = unitelabs.silas.TecanFluentClient(self.host, self.port)
        await self.client.connect()

    async def stop(self):
        """Stop the connection to the SiLA server."""
        if self.client is not None:
            await self.client.disconnect()
            self.client = None

    def serialize(self) -> dict:
        return {
            **super().serialize(),
            "num_channels": self.num_channels,
            "host": self.host,
            "port": self.port
        }

    async def pick_up_tips(self, ops: List["Pickup"], **backend_kwargs):
        """Pick up tips using the SiLA server."""
        if not self.client:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to SiLA commands
        for op in ops:
            tip_positions = [tip.get_absolute_location() for tip in op.tips]
            await self.client.pick_up_tips(tip_positions)

    async def drop_tips(self, ops: List["Drop"], **backend_kwargs):
        """Drop tips using the SiLA server."""
        if not self.client:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to SiLA commands
        for op in ops:
            tip_positions = [tip.get_absolute_location() for tip in op.tips]
            await self.client.drop_tips(tip_positions)

    async def aspirate(self, ops: List["SingleChannelAspiration"], **backend_kwargs):
        """Aspirate liquid using the SiLA server."""
        if not self.client:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to SiLA commands
        for op in ops:
            position = op.resource.get_absolute_location()
            await self.client.aspirate(
                position=position,
                volume=op.volume,
                flow_rate=op.flow_rate,
                liquid_height=op.liquid_height,
                blow_out=op.blow_out
            )

    async def dispense(self, ops: List["SingleChannelDispense"], **backend_kwargs):
        """Dispense liquid using the SiLA server."""
        if not self.client:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to SiLA commands
        for op in ops:
            position = op.resource.get_absolute_location()
            await self.client.dispense(
                position=position,
                volume=op.volume,
                flow_rate=op.flow_rate,
                liquid_height=op.liquid_height,
                blow_out=op.blow_out
            )

    async def pick_up_resource(self, ops: List["ResourcePickup"], **backend_kwargs):
        """Pick up a resource using the SiLA server."""
        if not self.client:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to SiLA commands
        for op in ops:
            position = op.resource.get_absolute_location()
            await self.client.pick_up_resource(position)

    async def move_picked_up_resource(self, ops: List["ResourceMove"], **backend_kwargs):
        """Move a picked up resource using the SiLA server."""
        if not self.client:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to SiLA commands
        for op in ops:
            position = op.resource.get_absolute_location()
            await self.client.move_resource(position)

    async def drop_resource(self, ops: List["ResourceDrop"], **backend_kwargs):
        """Drop a resource using the SiLA server."""
        if not self.client:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        # Convert PyLabRobot operations to SiLA commands
        for op in ops:
            position = op.resource.get_absolute_location()
            await self.client.drop_resource(position)