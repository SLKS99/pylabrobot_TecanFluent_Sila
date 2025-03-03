from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import UnitelabsSilasBackend
from pylabrobot.resources import Deck

async def main():
    # Create a backend instance
    backend = UnitelabsSilasBackend(
        num_channels=8,  # Adjust based on your Tecan Fluent configuration
        host="localhost",  # Change to your SiLA server host
        port=50051  # Change to your SiLA server port
    )

    # Create a deck from your layout file
    deck = Deck.load_from_json_file("tecan-layout.json")  # Create this file with your deck layout

    # Create liquid handler instance
    lh = LiquidHandler(backend=backend, deck=deck)

    # Setup the connection
    await lh.setup()

    try:
        # Example operation: Move 100uL from well A1 to A2
        await lh.pick_up_tips(lh.deck.get_resource("tip_rack")["A1"])
        await lh.aspirate(lh.deck.get_resource("plate")["A1"], vols=100)
        await lh.dispense(lh.deck.get_resource("plate")["A2"], vols=100)
        await lh.return_tips()

    finally:
        # Always clean up
        await lh.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())