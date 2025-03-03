import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TecanSimulator:
    """Simulates basic Tecan Fluent operations for testing"""

    def __init__(self):
        self.connected = False
        self.current_method = None
        self.labware = {}
        self.tip_states = {}  # Track which channels have tips
        self.liquid_states = {}  # Track liquid volumes in wells

    async def connect(self):
        """Simulate connecting to the device"""
        self.connected = True
        logger.info("Connected to simulated Tecan Fluent")

    async def disconnect(self):
        """Simulate disconnecting from the device"""
        self.connected = False
        logger.info("Disconnected from simulated Tecan Fluent")

    async def load_worklist(self, worklist_path: Path) -> List[Dict[str, Any]]:
        """Load and parse a worklist file"""
        if not worklist_path.exists():
            raise FileNotFoundError(f"Worklist file not found: {worklist_path}")

        commands = []
        for line in worklist_path.read_text().strip().split('\n'):
            if not line or line.isspace():
                continue

            parts = line.split(';')
            cmd = parts[0]

            if cmd == 'A':  # Aspirate
                commands.append({
                    'type': 'aspirate',
                    'plate': parts[1],
                    'well': parts[2],
                    'volume': float(parts[4])
                })
            elif cmd == 'D':  # Dispense
                commands.append({
                    'type': 'dispense',
                    'plate': parts[1],
                    'well': parts[2],
                    'volume': float(parts[4])
                })
            elif cmd == 'W':  # Wash
                commands.append({'type': 'wash'})
            elif cmd == 'B':  # Break
                commands.append({'type': 'break'})
            elif cmd == 'M':  # Mix
                commands.append({
                    'type': 'mix',
                    'plate': parts[1],
                    'well': parts[2],
                    'cycles': int(parts[3]),
                    'volume': float(parts[4])
                })

        return commands

    async def execute_commands(self, commands: List[Dict[str, Any]]):
        """Simulate executing a list of commands"""
        if not self.connected:
            raise RuntimeError("Not connected to simulator")

        for cmd in commands:
            cmd_type = cmd['type']

            if cmd_type == 'aspirate':
                logger.info(f"Simulating aspirate: {cmd['volume']}µL from {cmd['plate']} {cmd['well']}")
                await asyncio.sleep(0.5)  # Simulate operation time

            elif cmd_type == 'dispense':
                logger.info(f"Simulating dispense: {cmd['volume']}µL to {cmd['plate']} {cmd['well']}")
                await asyncio.sleep(0.5)

            elif cmd_type == 'wash':
                logger.info("Simulating tip wash")
                await asyncio.sleep(1.0)

            elif cmd_type == 'break':
                logger.info("Simulating break (pause)")
                await asyncio.sleep(0.2)

            elif cmd_type == 'mix':
                logger.info(f"Simulating mix: {cmd['cycles']} cycles of {cmd['volume']}µL in {cmd['plate']} {cmd['well']}")
                await asyncio.sleep(cmd['cycles'] * 0.3)

    def setup_labware(self, labware_config: Dict[str, Dict[str, Any]]):
        """Set up labware in the simulator"""
        self.labware = labware_config
        logger.info(f"Set up labware: {labware_config}")

    def get_status(self) -> Dict[str, Any]:
        """Get current simulator status"""
        return {
            'connected': self.connected,
            'current_method': self.current_method,
            'labware': self.labware,
            'tip_states': self.tip_states,
            'liquid_states': self.liquid_states
        }