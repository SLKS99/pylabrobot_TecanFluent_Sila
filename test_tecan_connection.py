import asyncio
import logging
import os
from typing import List

from pylabrobot.liquid_handling.backends.tecan.fluent import TecanFluentBackend
from pylabrobot.resources import TipRack, Plate, Well


class TecanConnectionTest:
    """Test class for verifying Tecan Fluent connection and operations."""

    def __init__(self, host: str = "localhost", port: int = 50051):
        """Initialize the test class.

        Args:
            host: The hostname where the Tecan Fluent Control server is running.
            port: The port number for the SiLA2 server.
        """
        self.backend = TecanFluentBackend(host=host, port=port)
        self.logger = logging.getLogger("tecan_test")

    async def setup(self):
        """Set up the connection and initialize resources."""
        try:
            await self.backend.setup()
            self.logger.info("Successfully connected to Tecan Fluent")
        except Exception as e:
            self.logger.error(f"Failed to connect to Tecan Fluent: {e}")
            raise

    async def test_basic_connection(self):
        """Test basic connection to the Tecan Fluent."""
        try:
            # Create a simple resource state
            tip_rack = TipRack("tip_rack_1", size_x=12, size_y=8)
            plate = Plate("plate_1", size_x=12, size_y=8)

            # Test if resources are recognized
            state1 = self.backend.get_resource_state(tip_rack)
            state2 = self.backend.get_resource_state(plate)

            self.logger.info("Basic connection test passed")
            return True
        except Exception as e:
            self.logger.error(f"Basic connection test failed: {e}")
            return False

    async def test_multi_channel_pipetting(self):
        """Test multi-channel pipetting operations."""
        try:
            # Set up resources
            tip_rack = TipRack("tip_rack_1", size_x=12, size_y=8)
            source_plate = Plate("source_plate", size_x=12, size_y=8)
            target_plate = Plate("target_plate", size_x=12, size_y=8)

            # Define test volumes
            volumes = [100.0, 150.0, 200.0, 250.0]  # Test different volumes

            # Pick up tips
            tips = tip_rack.get_tips([0, 1, 2, 3])  # Get first 4 tips
            await self.backend.pick_up_tips(tips)

            # Aspirate from source wells
            source_wells = [source_plate.get_well(0, i) for i in range(4)]
            await self.backend.aspirate(source_wells, volumes)

            # Dispense to target wells
            target_wells = [target_plate.get_well(1, i) for i in range(4)]
            await self.backend.dispense(target_wells, volumes)

            # Drop tips
            await self.backend.drop_tips(tips)

            self.logger.info("Multi-channel pipetting test passed")
            return True
        except Exception as e:
            self.logger.error(f"Multi-channel pipetting test failed: {e}")
            return False

    async def test_worklist_execution(self):
        """Test execution of a worklist file."""
        try:
            # Create a simple worklist file
            worklist_path = "worklist_tests/worklists/simple_transfer.gwl"
            os.makedirs(os.path.dirname(worklist_path), exist_ok=True)

            with open(worklist_path, "w") as f:
                f.write("A;aspirate;;100;;96WellMtx_1;;1;;1\n")
                f.write("D;dispense;;100;;96WellMtx_2;;1;;1\n")

            # Execute the worklist
            await self.backend.execute_worklist(worklist_path)

            self.logger.info("Worklist execution test passed")
            return True
        except Exception as e:
            self.logger.error(f"Worklist execution test failed: {e}")
            return False

    async def cleanup(self):
        """Clean up and disconnect from the Tecan Fluent."""
        try:
            await self.backend.stop()
            self.logger.info("Successfully disconnected from Tecan Fluent")
        except Exception as e:
            self.logger.error(f"Failed to disconnect from Tecan Fluent: {e}")
            raise


async def main():
    """Main function to run all tests."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create test instance
    test = TecanConnectionTest()

    try:
        # Setup
        await test.setup()

        # Run tests
        connection_ok = await test.test_basic_connection()
        if connection_ok:
            await test.test_multi_channel_pipetting()
            await test.test_worklist_execution()

        # Cleanup
        await test.cleanup()

    except Exception as e:
        logging.error(f"Test suite failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())