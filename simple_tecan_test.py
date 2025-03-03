"""Simple test script for PyLabRobot with Tecan Fluent."""

import asyncio
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends.tecan import TecanSiLABackend
from pylabrobot.resources import Deck, Coordinate
from pylabrobot.resources.tecan import TecanTipRack, TecanPlate

async def main():
    # Create a backend instance
    backend = TecanSiLABackend(
        num_channels=8,
        host="127.0.0.1",
        port=50052,
        insecure=True  # For testing only
    )

    # Create deck and liquid handler
    deck = Deck()
    lh = LiquidHandler(backend=backend, deck=deck)

    # Add resources to the deck
    tip_rack = TecanTipRack(
        name="tip_rack_1",
        size_x=127.76,
        size_y=85.48,
        size_z=92.0,
        model="Tecan 200uL Filter Tips"
    )
    deck.assign_child_resource(tip_rack, location=Coordinate(x=100, y=100, z=100))

    source_plate = TecanPlate(
        name="source_plate",
        size_x=127.76,
        size_y=85.48,
        size_z=14.0,
        model="Tecan 96 Well Plate"
    )
    deck.assign_child_resource(source_plate, location=Coordinate(x=200, y=100, z=100))

    try:
        print("Setting up connection to Tecan Fluent...")
        await lh.setup()

        print("Picking up tips...")
        await lh.pick_up_tips(tip_rack["A1"])

        print("Aspirating from source plate...")
        await lh.aspirate(
            resource=source_plate["A1"],
            volume=100,
            flow_rate=100,
            liquid_height=1.0
        )

        print("Operations completed successfully!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        print("Cleaning up...")
        await lh.stop()

if __name__ == "__main__":
    asyncio.run(main())