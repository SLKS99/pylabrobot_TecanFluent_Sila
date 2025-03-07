"""Tests for the Tecan Fluent backend."""

import pytest
from pylabrobot.liquid_handling.backends.tecan.fluent import Fluent

# Configuration
FLUENT_IP = "216.96.181.199"
FLUENT_PORT = 50052

@pytest.mark.asyncio
async def test_connect_to_fluent() -> None:
    """Test basic connection to Fluent SiLA server."""
    print("\n=== Testing Fluent Backend Connection ===")
    print(f"Connecting to SiLA server at {FLUENT_IP}:{FLUENT_PORT}")

    backend = Fluent(
        num_channels=8,
        host=FLUENT_IP,
        port=FLUENT_PORT,
        simulation_mode=False
    )

    try:
        await backend.setup()
        print("Successfully connected to Fluent server")

        # Test getting methods after connection
        methods = backend.get_available_methods()  # Synchronous call
        print(f"Available methods: {methods}")
        assert methods is not None
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        raise
    finally:
        await backend.stop()

@pytest.mark.asyncio
async def test_get_available_methods() -> None:
    """Test retrieving available methods from FluentControl."""
    backend = Fluent(
        num_channels=8,
        host=FLUENT_IP,
        port=FLUENT_PORT,
        simulation_mode=False
    )

    try:
        await backend.setup()

        # Get available methods (synchronous call)
        methods = backend.get_available_methods()
        print(f"Available methods: {methods}")
        assert methods is not None, "No methods available"
        assert len(methods) > 0, "No methods found in FluentControl"
    finally:
        await backend.stop()

@pytest.mark.asyncio
async def test_worklist_operations() -> None:
    """Test worklist operations with Fluent backend."""
    backend = Fluent(
        num_channels=8,
        host=FLUENT_IP,
        port=FLUENT_PORT
    )

    try:
        await backend.setup()

        # Get available methods (synchronous)
        print("\nGetting available methods...")
        methods = backend.get_available_methods()
        print(f"Available methods: {methods}")

        if len(methods) > 0:
            method_name = methods[0]  # Use the first available method
            print(f"\nUsing method: {method_name}")

            # Get method parameters
            try:
                params = await backend.get_method_parameters(method_name)
                print(f"Method parameters: {params}")
            except Exception as e:
                print(f"Error getting method parameters: {e}")

            # Add method to worklist
            print("\nAdding method to worklist...")
            success = await backend.add_to_worklist(method_name, {})
            print(f"Add to worklist success: {success}")

            # Get current worklist
            worklist = await backend.get_worklist()
            print(f"\nCurrent worklist: {worklist}")

            # Run the worklist
            print("\nRunning worklist...")
            success = await backend.run_worklist()
            print(f"Run worklist success: {success}")

            # Get worklist status
            status = await backend.get_worklist_status()
            print(f"Worklist status: {status}")

    finally:
        await backend.stop()

@pytest.mark.asyncio
async def test_liquid_handling_operations() -> None:
    """Test basic liquid handling operations."""
    backend = Fluent(
        num_channels=8,
        host=FLUENT_IP,
        port=FLUENT_PORT
    )

    try:
        await backend.setup()

        # Get available methods (synchronous)
        methods = backend.get_available_methods()
        print(f"Available methods: {methods}")
        assert len(methods) > 0, "No methods available"

        # Test basic liquid handling sequence
        print("\nTesting liquid handling sequence...")

        # First, get available labware from FluentControl
        print("Getting available labware...")
        try:
            labware = await backend.get_available_labware()
            print(f"Available labware: {labware}")

            if labware:
                source = labware[0]  # Use first available labware as source
                destination = labware[1] if len(labware) > 1 else labware[0]  # Use second if available, else same

                # Perform simple transfer
                print(f"\nAttempting transfer from {source} to {destination}")
                await backend.aspirate(source, volume=100)
                await backend.dispense(destination, volume=100)
                print("Transfer completed")

        except Exception as e:
            print(f"Error during liquid handling: {e}")

    finally:
        await backend.stop()