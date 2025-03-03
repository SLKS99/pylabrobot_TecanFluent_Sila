import asyncio
import logging
import sys
from unitelabs.tecan_fluentcontrol import FluentControlProtocol
from unitelabs.tecan_fluentcontrol.io.simulation import (
    ExecutionChannelSimulation,
    FluentControlSimulation,
    RuntimeControllerSimulation,
)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Force simulation mode
        sys.platform = "linux"  # This tricks the library into using simulation mode

        # Create FluentControl protocol instance
        protocol = FluentControlProtocol()

        # Try to open connection
        await protocol.open()
        logger.info("Successfully connected to Tecan Fluent Control (Simulation Mode)")

        # Get available workspaces
        workspaces = await protocol.fluent_control.get_workspaces()
        logger.info(f"Available workspaces: {workspaces}")

        # Test some basic operations
        await protocol.fluent_control.prepare_method("TestMethod")
        logger.info("Method preparation successful")

        # Close connection
        await protocol.close()
        logger.info("Connection closed successfully")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())