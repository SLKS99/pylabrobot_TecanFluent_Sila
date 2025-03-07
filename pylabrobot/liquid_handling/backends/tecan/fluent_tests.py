"""Tests for the Tecan Fluent backend."""

import asyncio
import pytest
from typing import Dict, Any

from pylabrobot.liquid_handling.backends.tecan.fluent import Fluent

@pytest.fixture
async def fluent_backend():
    """Create a Fluent backend instance for testing."""
    backend = Fluent(
        num_channels=8,
        host="127.0.0.1",
        port=50052,
        simulation_mode=True  # Use simulation mode for testing
    )
    await backend.setup()
    yield backend
    await backend.stop()

@pytest.mark.asyncio
async def test_method_management(fluent_backend):
    """Test method management functionality."""
    # Get available methods
    methods = await fluent_backend.get_available_methods()
    assert isinstance(methods, list)
    assert "simulation_method" in methods

    # Get method parameters
    params = await fluent_backend.get_method_parameters("simulation_method")
    assert isinstance(params, dict)
    assert "param1" in params
    assert "param2" in params

@pytest.mark.asyncio
async def test_worklist_management(fluent_backend):
    """Test worklist management functionality."""
    # Clear worklist
    success = await fluent_backend.clear_worklist()
    assert success is True

    # Add method to worklist
    method_params: Dict[str, Any] = {
        "param1": "value1",
        "param2": "value2"
    }
    success = await fluent_backend.add_to_worklist("simulation_method", method_params)
    assert success is True

    # Get worklist
    worklist = await fluent_backend.get_worklist()
    assert isinstance(worklist, list)
    assert len(worklist) > 0

@pytest.mark.asyncio
async def test_worklist_control(fluent_backend):
    """Test worklist control functionality."""
    # Run worklist
    success = await fluent_backend.run_worklist()
    assert success is True

    # Get worklist status
    status = await fluent_backend.get_worklist_status()
    assert isinstance(status, str)
    assert status == "Completed"

    # Test pause/resume
    success = await fluent_backend.pause_worklist()
    assert success is True

    status = await fluent_backend.get_worklist_status()
    assert status == "Paused"

    success = await fluent_backend.resume_worklist()
    assert success is True

    # Test stop
    success = await fluent_backend.stop_worklist()
    assert success is True

    status = await fluent_backend.get_worklist_status()
    assert status == "Stopped"

@pytest.mark.asyncio
async def test_worklist_sequence(fluent_backend):
    """Test a complete worklist sequence."""
    # Clear existing worklist
    await fluent_backend.clear_worklist()

    # Add multiple methods to worklist
    methods = [
        ("method1", {"param1": "value1"}),
        ("method2", {"param2": "value2"}),
        ("method3", {"param3": "value3"})
    ]

    for method_name, params in methods:
        success = await fluent_backend.add_to_worklist(method_name, params)
        assert success is True

    # Verify worklist contents
    worklist = await fluent_backend.get_worklist()
    assert len(worklist) == len(methods)

    # Run worklist
    success = await fluent_backend.run_worklist()
    assert success is True

    # Monitor status
    while True:
        status = await fluent_backend.get_worklist_status()
        if status == "Completed":
            break
        await asyncio.sleep(0.1)  # Small delay to prevent busy waiting