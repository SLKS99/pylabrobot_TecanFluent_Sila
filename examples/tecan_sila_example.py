import asyncio
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import TecanSiLABackend
from pylabrobot.resources import Deck, Coordinate
from pylabrobot.resources.tecan import TecanTipRack, TecanPlate

async def main():
    # Create a backend instance with FluentControl support
    backend = TecanSiLABackend(
        num_channels=8,  # Adjust based on your Tecan Fluent configuration
        host="localhost",  # Change to your SiLA server host
        port=50051,  # Change to your SiLA server port
        method_name="MyWorkflow"  # Optional: specify a FluentControl method name
    )

    # Create a deck
    deck = Deck()

    # Add resources to the deck with carrier information
    tip_rack = TecanTipRack(
        name="tip_rack_1",  # This name should match the carrier name in FluentControl
        size_x=127.76,
        size_y=85.48,
        size_z=92.0,
        model="Tecan 200uL Filter Tips"
    )
    deck.assign_child_resource(tip_rack, location=Coordinate(x=100, y=100, z=100))

    source_plate = TecanPlate(
        name="source_plate_1",  # This name should match the carrier name in FluentControl
        size_x=127.76,
        size_y=85.48,
        size_z=14.0,
        model="Tecan 96 Well Plate"
    )
    deck.assign_child_resource(source_plate, location=Coordinate(x=200, y=100, z=100))

    destination_plate = TecanPlate(
        name="destination_plate_1",  # This name should match the carrier name in FluentControl
        size_x=127.76,
        size_y=85.48,
        size_z=14.0,
        model="Tecan 96 Well Plate"
    )
    deck.assign_child_resource(destination_plate, location=Coordinate(x=300, y=100, z=100))

    # Create liquid handler instance
    lh = LiquidHandler(backend=backend, deck=deck)

    # Setup the connection
    print("Setting up connection to Tecan Fluent...")
    await lh.setup()

    try:
        print("Running liquid handling operations...")

        # Pick up tips
        print("Picking up tips...")
        await lh.pick_up_tips(tip_rack["A1"])

        # Aspirate from source well with liquid class
        print("Aspirating...")
        await lh.aspirate(
            resource=source_plate["A1"],
            vols=100,
            flow_rate=100,
            liquid_height=1.0,
            blow_out=True,
            backend_kwargs={"liquid_class": "Water"}  # Specify liquid class
        )

        # Dispense to destination well
        print("Dispensing...")
        await lh.dispense(
            resource=destination_plate["A1"],
            vols=100,
            flow_rate=100,
            liquid_height=1.0,
            blow_out=True,
            backend_kwargs={"liquid_class": "Water"}  # Use same liquid class
        )

        # Return tips
        print("Dropping tips...")
        await lh.return_tips()

        print("Operations completed successfully!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

    finally:
        # Always clean up
        print("Cleaning up...")
        await lh.stop()

if __name__ == "__main__":
    print("Starting Tecan Fluent FluentControl example...")
    asyncio.run(main())