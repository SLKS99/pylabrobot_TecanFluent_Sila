import asyncio
import logging
from typing import List, Optional, Tuple, Union

import sila2
from unitelabs.tecan_fluentcontrol.client import TecanFluentControlClient


class TecanFluentConnection:
    """Connection handler for Tecan Fluent using SiLA2."""

    def __init__(self, host: str = "localhost", port: int = 50051):
        """Initialize the connection handler.

        Args:
            host: The hostname where the Tecan Fluent Control server is running.
            port: The port number for the SiLA2 server.
        """
        self.logger = logging.getLogger("pylabrobot.tecan.fluent.connection")
        self.host = host
        self.port = port
        self.client: Optional[TecanFluentControlClient] = None

    async def connect(self):
        """Connect to the Tecan Fluent Control server."""
        try:
            self.client = TecanFluentControlClient(self.host, self.port)
            await self.client.connect()
            self.logger.info(f"Connected to Tecan Fluent Control at {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Tecan Fluent Control: {e}")
            raise

    async def disconnect(self):
        """Disconnect from the Tecan Fluent Control server."""
        if self.client:
            await self.client.disconnect()
            self.client = None
            self.logger.info("Disconnected from Tecan Fluent Control")

    async def pick_up_tips(self, positions: List[Tuple[float, float, float]]):
        """Pick up tips from specified positions.

        Args:
            positions: List of (x, y, z) coordinates for tip pickup.
        """
        if not self.client:
            raise RuntimeError("Not connected to Tecan Fluent Control")

        try:
            await self.client.pick_up_tips(positions)
            self.logger.info(f"Picked up tips from {len(positions)} positions")
        except Exception as e:
            self.logger.error(f"Failed to pick up tips: {e}")
            raise

    async def drop_tips(self, positions: List[Tuple[float, float, float]]):
        """Drop tips at specified positions.

        Args:
            positions: List of (x, y, z) coordinates for tip drop.
        """
        if not self.client:
            raise RuntimeError("Not connected to Tecan Fluent Control")

        try:
            await self.client.drop_tips(positions)
            self.logger.info(f"Dropped tips at {len(positions)} positions")
        except Exception as e:
            self.logger.error(f"Failed to drop tips: {e}")
            raise

    async def aspirate(self, positions: List[Tuple[float, float, float]], volumes: List[float]):
        """Aspirate liquid from specified positions.

        Args:
            positions: List of (x, y, z) coordinates for aspiration.
            volumes: List of volumes to aspirate in microliters.
        """
        if not self.client:
            raise RuntimeError("Not connected to Tecan Fluent Control")

        try:
            await self.client.aspirate(positions, volumes)
            self.logger.info(f"Aspirated {volumes} µL from {len(positions)} positions")
        except Exception as e:
            self.logger.error(f"Failed to aspirate: {e}")
            raise

    async def dispense(self, positions: List[Tuple[float, float, float]], volumes: List[float]):
        """Dispense liquid to specified positions.

        Args:
            positions: List of (x, y, z) coordinates for dispensing.
            volumes: List of volumes to dispense in microliters.
        """
        if not self.client:
            raise RuntimeError("Not connected to Tecan Fluent Control")

        try:
            await self.client.dispense(positions, volumes)
            self.logger.info(f"Dispensed {volumes} µL to {len(positions)} positions")
        except Exception as e:
            self.logger.error(f"Failed to dispense: {e}")
            raise

    async def execute_worklist(self, worklist_path: str):
        """Execute a Tecan worklist file.

        Args:
            worklist_path: Path to the worklist file.
        """
        if not self.client:
            raise RuntimeError("Not connected to Tecan Fluent Control")

        try:
            await self.client.execute_worklist(worklist_path)
            self.logger.info(f"Executed worklist: {worklist_path}")
        except Exception as e:
            self.logger.error(f"Failed to execute worklist: {e}")
            raise
