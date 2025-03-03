from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional, Union, Any

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
from pylabrobot.resources import Resource, Deck
from pylabrobot.resources.tip_tracker import TipTracker

logger = logging.getLogger(__name__)

class SimulatedRuntime:
    """Pure Python simulation of Tecan runtime functionality."""

    def __init__(self):
        self.initialized = False
        self.commands = []
        self.state = "idle"

    async def initialize(self):
        self.initialized = True
        self.state = "ready"
        logger.info("Runtime initialized")

    async def execute_command(self, command: str, params: dict):
        if not self.initialized:
            raise RuntimeError("Runtime not initialized")
        self.commands.append((command, params))
        logger.debug(f"Executed command {command} with params {params}")

    def get_status(self) -> dict:
        return {
            "initialized": self.initialized,
            "state": self.state,
            "command_count": len(self.commands)
        }

class SimulatedFluentControl:
    """Pure Python simulation of Tecan FluentControl."""

    def __init__(self):
        self.started = False
        self.runtime = SimulatedRuntime()

    async def start(self):
        self.started = True
        logger.info("FluentControl simulation started")

    async def stop(self):
        self.started = False
        logger.info("FluentControl simulation stopped")

    def get_status(self) -> dict:
        return {
            "started": self.started,
            "runtime_status": self.runtime.get_status() if self.started else None
        }

class TecanFluentSimulatorBackend(LiquidHandlerBackend):
    """Simulation backend for Tecan Fluent operations that follows UniteLabsSila's wrapper pattern."""

    def __init__(self):
        super().__init__()
        # Initialize pure Python simulation components
        self._fluent_control = SimulatedFluentControl()
        self._runtime_controller = self._fluent_control.runtime
        self._num_channels = 8
        self._tip_states = {}
        self._liquid_states = {}
        self._resources = {}
        self._picked_up_resource = None
        self.setup_finished = False

    def set_deck(self, deck: Deck):
        """Set the deck for the robot."""
        logger.info(f"Setting deck: {deck.name}")
        self._deck = deck

    def set_heads(self, head: Dict[int, TipTracker], head96: Optional[Dict[int, TipTracker]] = None):
        """Set the tip tracker for the robot."""
        logger.info("Setting heads")
        self._head = head
        self._head96 = head96

    @property
    def num_channels(self) -> int:
        return self._num_channels

    async def setup(self):
        """Set up the simulated connection."""
        await super().setup()
        logger.info("Setting up Tecan Fluent simulator")

        await self._fluent_control.start()
        await self._runtime_controller.initialize()
        self.setup_finished = True
        logger.info("Tecan Fluent simulator ready")

    async def stop(self):
        """Stop the simulated connection."""
        logger.info("Stopping Tecan Fluent simulator")
        await self._fluent_control.stop()
        self.setup_finished = False

    async def pick_up_tips(self, ops: List[Pickup], use_channels: List[int]):
        """Simulate picking up tips."""
        if not self.setup_finished:
            raise RuntimeError("Simulator not set up")

        for op, channel in zip(ops, use_channels):
            pos = op.resource.get_absolute_location()
            logger.info(f"Simulating tip pickup from {op.resource.name} at position ({pos.x}, {pos.y}, {pos.z}) using channel {channel}")
            await self._runtime_controller.execute_command("PickUpTip", {
                "channel": channel,
                "position": {"x": pos.x, "y": pos.y, "z": pos.z}
            })
            self._tip_states[channel] = True
            await asyncio.sleep(0.5)

    async def drop_tips(self, ops: List[Drop], use_channels: List[int]):
        """Simulate dropping tips."""
        if not self.setup_finished:
            raise RuntimeError("Simulator not set up")

        for op, channel in zip(ops, use_channels):
            pos = op.resource.get_absolute_location()
            logger.info(f"Simulating tip drop at {op.resource.name} at position ({pos.x}, {pos.y}, {pos.z}) using channel {channel}")
            await self._runtime_controller.execute_command("DropTip", {
                "channel": channel,
                "position": {"x": pos.x, "y": pos.y, "z": pos.z}
            })
            self._tip_states[channel] = False
            await asyncio.sleep(0.5)

    async def aspirate(self, ops: List[SingleChannelAspiration], use_channels: List[int]):
        """Simulate aspirating liquid."""
        if not self.setup_finished:
            raise RuntimeError("Simulator not set up")

        for op, channel in zip(ops, use_channels):
            if not self._tip_states.get(channel, False):
                raise RuntimeError(f"No tip on channel {channel}")

            pos = op.resource.get_absolute_location()
            logger.info(
                f"Simulating aspiration of {op.volume}µL from {op.resource.name} "
                f"at position ({pos.x}, {pos.y}, {pos.z}) using channel {channel}"
            )

            await self._runtime_controller.execute_command("Aspirate", {
                "channel": channel,
                "volume": op.volume,
                "position": {"x": pos.x, "y": pos.y, "z": pos.z},
                "liquid_class": op.liquid_class
            })

            well_key = f"{op.resource.name}_{op.resource.get_name()}"
            current_volume = self._liquid_states.get(well_key, 0)
            if current_volume < op.volume:
                raise RuntimeError(f"Not enough liquid in {well_key}")

            self._liquid_states[well_key] = current_volume - op.volume
            await asyncio.sleep(0.5)

    async def dispense(self, ops: List[SingleChannelDispense], use_channels: List[int]):
        """Simulate dispensing liquid."""
        if not self.setup_finished:
            raise RuntimeError("Simulator not set up")

        for op, channel in zip(ops, use_channels):
            if not self._tip_states.get(channel, False):
                raise RuntimeError(f"No tip on channel {channel}")

            pos = op.resource.get_absolute_location()
            logger.info(
                f"Simulating dispense of {op.volume}µL to {op.resource.name} "
                f"at position ({pos.x}, {pos.y}, {pos.z}) using channel {channel}"
            )

            await self._runtime_controller.execute_command("Dispense", {
                "channel": channel,
                "volume": op.volume,
                "position": {"x": pos.x, "y": pos.y, "z": pos.z},
                "liquid_class": op.liquid_class
            })

            well_key = f"{op.resource.name}_{op.resource.get_name()}"
            current_volume = self._liquid_states.get(well_key, 0)
            self._liquid_states[well_key] = current_volume + op.volume
            await asyncio.sleep(0.5)

    async def pick_up_tips96(self, pickup: PickupTipRack):
        """Simulate picking up tips with 96-head."""
        if not self.setup_finished:
            raise RuntimeError("Simulator not set up")

        logger.info(f"Simulating 96-head tip pickup from {pickup.resource.name}")
        await self._runtime_controller.execute_command("PickUpTips96", {
            "resource": pickup.resource.name
        })
        await asyncio.sleep(1.0)

    async def drop_tips96(self, drop: DropTipRack):
        """Simulate dropping tips with 96-head."""
        if not self.setup_finished:
            raise RuntimeError("Simulator not set up")

        logger.info(f"Simulating 96-head tip drop to {drop.resource.name}")
        await self._runtime_controller.execute_command("DropTips96", {
            "resource": drop.resource.name
        })
        await asyncio.sleep(1.0)

    async def aspirate96(self, aspiration: Union[MultiHeadAspirationPlate, MultiHeadAspirationContainer]):
        """Simulate aspirating with 96-head."""
        if not self.setup_finished:
            raise RuntimeError("Simulator not set up")

        logger.info(f"Simulating 96-head aspiration from {aspiration.resource.name}")
        await self._runtime_controller.execute_command("Aspirate96", {
            "resource": aspiration.resource.name,
            "volume": aspiration.volume
        })
        await asyncio.sleep(1.0)

    async def dispense96(self, dispense: Union[MultiHeadDispensePlate, MultiHeadDispenseContainer]):
        """Simulate dispensing with 96-head."""
        if not self.setup_finished:
            raise RuntimeError("Simulator not set up")

        logger.info(f"Simulating 96-head dispense to {dispense.resource.name}")
        await self._runtime_controller.execute_command("Dispense96", {
            "resource": dispense.resource.name,
            "volume": dispense.volume
        })
        await asyncio.sleep(1.0)

    async def pick_up_resource(self, pickup: ResourcePickup):
        """Simulate picking up a resource."""
        if not self.setup_finished:
            raise RuntimeError("Simulator not set up")
        if self._picked_up_resource is not None:
            raise RuntimeError("Already holding a resource")

        logger.info(f"Simulating resource pickup: {pickup.resource.name}")
        await self._runtime_controller.execute_command("PickUpResource", {
            "resource": pickup.resource.name
        })
        self._picked_up_resource = pickup.resource
        await asyncio.sleep(1.0)

    async def move_picked_up_resource(self, move: ResourceMove):
        """Simulate moving a picked up resource."""
        if not self.setup_finished:
            raise RuntimeError("Simulator not set up")
        if self._picked_up_resource is None:
            raise RuntimeError("No resource picked up")

        logger.info(
            f"Simulating moving resource {move.resource.name} to "
            f"({move.target_location.x}, {move.target_location.y}, {move.target_location.z})"
        )
        await self._runtime_controller.execute_command("MoveResource", {
            "resource": move.resource.name,
            "target": {
                "x": move.target_location.x,
                "y": move.target_location.y,
                "z": move.target_location.z
            }
        })
        await asyncio.sleep(1.0)

    async def drop_resource(self, drop: ResourceDrop):
        """Simulate dropping a resource."""
        if not self.setup_finished:
            raise RuntimeError("Simulator not set up")
        if self._picked_up_resource is None:
            raise RuntimeError("No resource picked up")

        logger.info(f"Simulating resource drop: {drop.resource.name}")
        await self._runtime_controller.execute_command("DropResource", {
            "resource": drop.resource.name
        })
        self._picked_up_resource = None
        await asyncio.sleep(1.0)

    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get a loaded resource by ID."""
        return self._resources.get(resource_id)

    def get_status(self) -> Dict[str, Any]:
        """Get current simulator status."""
        return {
            'setup_finished': self.setup_finished,
            'fluent_control_status': self._fluent_control.get_status(),
            'tip_states': self._tip_states,
            'liquid_states': self._liquid_states,
            'resources': {k: v.name for k, v in self._resources.items()},
            'picked_up_resource': self._picked_up_resource.name if self._picked_up_resource else None
        }