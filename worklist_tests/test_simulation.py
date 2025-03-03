import asyncio
import logging
from pathlib import Path

from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.resources.corning_costar.plates import Cor_96_wellplate_360ul_Fb
from pylabrobot.resources import TipRack, Deck
from tecan_simulator_backend import TecanFluentSimulatorBackend

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def main():
    # Initialize the simulator backend
    backend = TecanFluentSimulatorBackend()

    # Create a deck for the liquid handler
    deck = Deck(size_x=1000, size_y=500, size_z=400)

    # Create a liquid handler with the simulator backend and deck
    lh = LiquidHandler(backend=backend, deck=deck)
    logger.info("Created liquid handler with simulator backend")

    try:
        # Set up the liquid handler
        logger.info("Setting up liquid handler...")
        await lh.setup()

        # Create resources (plates and tip rack)
        tiprack = TipRack(
            name="tiprack",
            size_x=127.76,
            size_y=85.48,
            size_z=92.0,
            model="Cos_96_EZWash"
        )

        source_plate = Cor_96_wellplate_360ul_Fb(
            name="source_plate"
        )

        destination_plate = Cor_96_wellplate_360ul_Fb(
            name="destination_plate"
        )

        logger.info("Created labware resources")

        # Load resources onto the deck
        logger.info("Loading resources...")
        await lh.load_resource(tiprack, location={"x": 0, "y": 0, "z": 0})
        await lh.load_resource(source_plate, location={"x": 150, "y": 0, "z": 0})
        await lh.load_resource(destination_plate, location={"x": 300, "y": 0, "z": 0})
        logger.info("Resources loaded")

        # Initialize source plate with some liquid
        source_wells = ["A1", "B1", "C1", "D1", "E1", "F1", "G1", "H1"]
        for well in source_wells:
            well_key = f"source_plate_{well}"
            backend._liquid_states[well_key] = 1000  # 1000µL in each well

        # Simulate a simple transfer
        logger.info("Starting simulated transfer...")

        # Pick up tips from the first row
        logger.info("Picking up tips...")
        await lh.pick_up_tips(tiprack["A1:H1"])
        logger.info("Tips picked up")

        # Aspirate from source plate
        logger.info("Aspirating from source plate...")
        await lh.aspirate(
            resource=source_plate["A1:H1"],
            volume=100,  # Volume in µL
            flow_rate=100,  # Flow rate in µL/s
            liquid_class="water"
        )
        logger.info("Aspiration complete")

        # Dispense to destination plate
        logger.info("Dispensing to destination plate...")
        await lh.dispense(
            resource=destination_plate["A1:H1"],
            volume=100,
            flow_rate=100,
            liquid_class="water"
        )
        logger.info("Dispense complete")

        # Drop tips
        logger.info("Dropping tips...")
        await lh.drop_tips(tiprack["A1:H1"])
        logger.info("Tips dropped")

        # Get final simulator status
        status = backend.get_status()
        logger.info(f"Final simulator status: {status}")

        logger.info("Simulation completed successfully!")

    except Exception as e:
        logger.error(f"Error during simulation: {e}")
        raise

    finally:
        # Clean up
        logger.info("Cleaning up...")
        await lh.stop()
        logger.info("Cleanup complete")

if __name__ == "__main__":
    asyncio.run(main())