import asyncio
import logging
from pathlib import Path
from tecan_simulator import TecanSimulator

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Example worklist content
EXAMPLE_WORKLIST = """
A;Source_96;A1;;50
D;Dest_96;A1;;50
W;
B;
A;Source_96;A2;;100
D;Dest_96;A2;;100
M;Dest_96;A2;3;100
"""

async def create_worklist():
    """Create a sample worklist file"""
    worklist_dir = Path("worklist_tests/worklists")
    worklist_dir.mkdir(exist_ok=True)

    worklist_path = worklist_dir / "simple_transfer.gwl"
    worklist_path.write_text(EXAMPLE_WORKLIST.strip())
    return worklist_path

async def main():
    try:
        # Create and set up simulator
        simulator = TecanSimulator()

        # Create worklist file
        worklist_path = await create_worklist()
        logger.info(f"Created worklist file at: {worklist_path}")

        # Connect to simulator
        await simulator.connect()

        # Set up labware
        labware_config = {
            "Source_96": {
                "type": "96 Well Plate",
                "position": "1",
                "category": "plate"
            },
            "Dest_96": {
                "type": "96 Well Plate",
                "position": "2",
                "category": "plate"
            },
            "Tiprack": {
                "type": "96 Position Tiprack",
                "position": "3",
                "category": "tiprack"
            }
        }
        simulator.setup_labware(labware_config)

        # Load and parse worklist
        commands = await simulator.load_worklist(worklist_path)
        logger.info(f"Loaded {len(commands)} commands from worklist")

        # Execute commands
        await simulator.execute_commands(commands)

        # Get final status
        status = simulator.get_status()
        logger.info(f"Final simulator status: {status}")

        # Disconnect
        await simulator.disconnect()

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())