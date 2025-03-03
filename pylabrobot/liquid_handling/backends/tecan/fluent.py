import asyncio
import logging
from typing import List, Optional, Tuple, Union

from pylabrobot.liquid_handling.backends.backend import LiquidHandlerBackend
from pylabrobot.liquid_handling.standard import (
    Pickup,
    Drop,
    Aspiration,
    Dispense,
    ResourceState,
    TipTransfer
)
from pylabrobot.resources import Resource, Tip, TipRack, Plate, Well
from .fluent_connection import TecanFluentConnection


class TecanFluentBackend(LiquidHandlerBackend):
    """Backend for Tecan Fluent liquid handler using SiLA2."""

    def __init__(self, host: str = "localhost", port: int = 50051):
        """Initialize the Tecan Fluent backend.

        Args:
            host: The hostname where the Tecan Fluent Control server is running.
            port: The port number for the SiLA2 server.
        """
        super().__init__()
        self.logger = logging.getLogger("pylabrobot.tecan.fluent")
        self.connection = TecanFluentConnection(host=host, port=port)
        self._current_tips: List[Optional[Tip]] = [None] * 96  # Support for up to 96 channels

    async def setup(self):
        """Set up the connection to the Tecan Fluent."""
        await self.connection.connect()
        self.logger.info("Connected to Tecan Fluent")

    async def stop(self):
        """Stop the connection to the Tecan Fluent."""
        await self.connection.disconnect()
        self.logger.info("Disconnected from Tecan Fluent")

    async def pick_up_tips(self, pickup: Pickup, resource_state: ResourceState):
        """Pick up tips from specified positions."""
        tips = pickup.tips
        if not isinstance(tips[0].parent, TipRack):
            raise ValueError("Tips must be in a tip rack")

        positions = [tip.get_absolute_location() for tip in tips]
        await self.connection.pick_up_tips(positions)

        for i, tip in enumerate(tips):
            self._current_tips[i] = tip

        self.logger.info(f"Picked up {len(tips)} tips from {tips[0].parent}")

    async def drop_tips(self, drop: Drop, resource_state: ResourceState):
        """Drop tips at specified positions."""
        tips = drop.tips
        if not isinstance(tips[0].parent, TipRack):
            raise ValueError("Tips must be dropped in a tip rack")

        positions = [tip.get_absolute_location() for tip in tips]
        await self.connection.drop_tips(positions)

        for i, _ in enumerate(tips):
            self._current_tips[i] = None

        self.logger.info(f"Dropped {len(tips)} tips at {tips[0].parent}")

    async def aspirate(self, aspiration: Aspiration, resource_state: ResourceState):
        """Aspirate liquid from specified wells."""
        wells = aspiration.wells
        volumes = aspiration.volumes

        if not isinstance(wells[0].parent, Plate):
            raise ValueError("Can only aspirate from plates")

        positions = [well.get_absolute_location() for well in wells]
        await self.connection.aspirate(positions, volumes)

        self.logger.info(f"Aspirated {volumes} µL from {wells[0].parent}")

    async def dispense(self, dispense: Dispense, resource_state: ResourceState):
        """Dispense liquid to specified wells."""
        wells = dispense.wells
        volumes = dispense.volumes

        if not isinstance(wells[0].parent, Plate):
            raise ValueError("Can only dispense to plates")

        positions = [well.get_absolute_location() for well in wells]
        await self.connection.dispense(positions, volumes)

        self.logger.info(f"Dispensed {volumes} µL to {wells[0].parent}")

    async def execute_worklist(self, worklist_path: str):
        """Execute a Tecan worklist file."""
        await self.connection.execute_worklist(worklist_path)
        self.logger.info(f"Executed worklist: {worklist_path}")

    def get_resource_state(self, resource: Resource) -> ResourceState:
        """Get the state of a resource."""
        return ResourceState()
