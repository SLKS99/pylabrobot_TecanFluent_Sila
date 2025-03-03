"""Backend implementation for controlling Tecan Fluent using the official Tecan Fluent SiLA2 connector."""

from typing import Any, Dict, List, Optional
from pylabrobot.liquid_handling.backends.backend import LiquidHandlerBackend
from pylabrobot.resources import Resource

try:
    from tecan import Fluent  # type: ignore
    HAS_TECAN_SILA = True
except ImportError:
    HAS_TECAN_SILA = False

class TecanSiLABackend(LiquidHandlerBackend):
    """A backend that uses the official Tecan Fluent SiLA2 connector to control a Tecan Fluent."""

    def __init__(
        self,
        num_channels: int,
        host: str = "127.0.0.1",
        port: int = 50052,
        insecure: bool = True,
        username: str = None,
        password: str = None,
        discovery_time: int = 10
    ):
        """Create a new TecanSiLA backend.

        Args:
            num_channels: The number of channels on the liquid handler.
            host: The hostname where the Tecan Fluent SiLA server is running.
            port: The port where the Tecan Fluent SiLA server is running.
            insecure: Whether to use insecure connection (no SSL).
            username: Username for UMS authentication (optional).
            password: Password for UMS authentication (optional).
            discovery_time: Time in seconds to wait for server discovery (optional).
        """
        if not HAS_TECAN_SILA:
            raise RuntimeError(
                "The TecanSiLA backend requires the Tecan Fluent SiLA2 connector. "
                "Please install it from: https://gitlab.com/tecan/fluent-sila2-connector"
            )

        super().__init__()
        self._num_channels = num_channels
        self.host = host
        self.port = port
        self.insecure = insecure
        self.username = username
        self.password = password
        self.discovery_time = discovery_time
        self.fluent = None

    @property
    def num_channels(self) -> int:
        return self._num_channels

    async def setup(self):
        """Set up the connection to the Tecan Fluent SiLA server."""
        await super().setup()

        try:
            # Try discovery first if host is not specified
            if self.host is None:
                self.fluent = Fluent.discover(self.discovery_time)
            else:
                self.fluent = Fluent(
                    self.host,
                    self.port,
                    insecure=self.insecure
                )

            # Start Fluent with optional UMS credentials
            if self.username and self.password:
                self.fluent.start_fluent(
                    username=self.username,
                    password=self.password
                )
            else:
                self.fluent.start_fluent()

        except Exception as e:
            raise RuntimeError(f"Failed to connect to Tecan Fluent: {str(e)}")

    async def stop(self):
        """Stop the connection to the Tecan Fluent SiLA server."""
        if self.fluent is not None:
            try:
                self.fluent.stop_fluent()
            except Exception:
                pass  # Ignore errors during cleanup
            self.fluent = None

    def serialize(self) -> dict:
        return {
            **super().serialize(),
            "num_channels": self.num_channels,
            "host": self.host,
            "port": self.port,
            "insecure": self.insecure,
            "username": self.username,
            "password": "***" if self.password else None
        }

    async def pick_up_tips(self, ops: List["Pickup"], **backend_kwargs):
        """Pick up tips using the Tecan Fluent."""
        if not self.fluent:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        for op in ops:
            for tip in op.tips:
                pos = tip.get_absolute_location()
                # Convert PyLabRobot coordinates to Fluent coordinates
                await self.fluent.pick_up_tip(
                    x=pos.x,
                    y=pos.y,
                    z=pos.z,
                    **backend_kwargs
                )

    async def drop_tips(self, ops: List["Drop"], **backend_kwargs):
        """Drop tips using the Tecan Fluent."""
        if not self.fluent:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        for op in ops:
            for tip in op.tips:
                pos = tip.get_absolute_location()
                await self.fluent.drop_tip(
                    x=pos.x,
                    y=pos.y,
                    z=pos.z,
                    **backend_kwargs
                )

    async def aspirate(self, ops: List["SingleChannelAspiration"], **backend_kwargs):
        """Aspirate liquid using the Tecan Fluent."""
        if not self.fluent:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        for op in ops:
            pos = op.resource.get_absolute_location()
            await self.fluent.aspirate(
                x=pos.x,
                y=pos.y,
                z=pos.z,
                volume=op.volume,
                flow_rate=op.flow_rate,
                liquid_height=op.liquid_height,
                blow_out=op.blow_out,
                **backend_kwargs
            )

    async def dispense(self, ops: List["SingleChannelDispense"], **backend_kwargs):
        """Dispense liquid using the Tecan Fluent."""
        if not self.fluent:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        for op in ops:
            pos = op.resource.get_absolute_location()
            await self.fluent.dispense(
                x=pos.x,
                y=pos.y,
                z=pos.z,
                volume=op.volume,
                flow_rate=op.flow_rate,
                liquid_height=op.liquid_height,
                blow_out=op.blow_out,
                **backend_kwargs
            )

    async def pick_up_resource(self, ops: List["ResourcePickup"], **backend_kwargs):
        """Pick up a resource using the Tecan Fluent."""
        if not self.fluent:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        for op in ops:
            pos = op.resource.get_absolute_location()
            await self.fluent.pick_up_labware(
                x=pos.x,
                y=pos.y,
                z=pos.z,
                **backend_kwargs
            )

    async def move_picked_up_resource(self, ops: List["ResourceMove"], **backend_kwargs):
        """Move a picked up resource using the Tecan Fluent."""
        if not self.fluent:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        for op in ops:
            pos = op.resource.get_absolute_location()
            await self.fluent.move_labware(
                x=pos.x,
                y=pos.y,
                z=pos.z,
                **backend_kwargs
            )

    async def drop_resource(self, ops: List["ResourceDrop"], **backend_kwargs):
        """Drop a resource using the Tecan Fluent."""
        if not self.fluent:
            raise RuntimeError("Backend not set up. Did you call setup()?")

        for op in ops:
            pos = op.resource.get_absolute_location()
            await self.fluent.place_labware(
                x=pos.x,
                y=pos.y,
                z=pos.z,
                **backend_kwargs
            )