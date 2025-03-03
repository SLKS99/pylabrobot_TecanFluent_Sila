"""Tests for the TecanSiLA backend."""

import asyncio
import pytest
from unittest.mock import MagicMock, patch

from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends.tecan.sila import TecanSiLABackend
from pylabrobot.resources import Coordinate, Resource, TipRack, Plate

# Mock the Tecan Fluent client
@pytest.fixture
def mock_fluent():
    with patch("pylabrobot.liquid_handling.backends.tecan.sila.Fluent") as mock:
        fluent_instance = MagicMock()
        mock.return_value = fluent_instance
        yield fluent_instance

@pytest.fixture
def backend(mock_fluent):
    return TecanSiLABackend(
        num_channels=8,
        host="127.0.0.1",
        port=50052,
        insecure=True
    )

@pytest.fixture
def liquid_handler(backend):
    lh = LiquidHandler(backend=backend)
    return lh

@pytest.mark.asyncio
async def test_setup_with_direct_connection(mock_fluent, backend):
    """Test setting up the backend with direct connection."""
    await backend.setup()
    mock_fluent.assert_called_once_with("127.0.0.1", 50052, insecure=True)
    mock_fluent.return_value.start_fluent.assert_called_once_with()

@pytest.mark.asyncio
async def test_setup_with_discovery(mock_fluent):
    """Test setting up the backend using discovery."""
    backend = TecanSiLABackend(num_channels=8, host=None)
    await backend.setup()
    mock_fluent.discover.assert_called_once_with(10)

@pytest.mark.asyncio
async def test_setup_with_ums_credentials(mock_fluent):
    """Test setting up the backend with UMS credentials."""
    backend = TecanSiLABackend(
        num_channels=8,
        username="test_user",
        password="test_pass"
    )
    await backend.setup()
    mock_fluent.return_value.start_fluent.assert_called_once_with(
        username="test_user",
        password="test_pass"
    )

@pytest.mark.asyncio
async def test_stop(mock_fluent, backend):
    """Test stopping the backend."""
    await backend.setup()
    await backend.stop()
    mock_fluent.return_value.stop_fluent.assert_called_once()

@pytest.mark.asyncio
async def test_pick_up_tips(mock_fluent, liquid_handler):
    """Test picking up tips."""
    tip_rack = TipRack(
        name="tip_rack",
        size_x=127.76,
        size_y=85.48,
        size_z=92.0,
        model="Tecan 200uL Filter Tips"
    )
    liquid_handler.deck.assign_child_resource(
        tip_rack,
        location=Coordinate(x=100, y=100, z=100)
    )

    await liquid_handler.setup()
    await liquid_handler.pick_up_tips(tip_rack["A1"])

    mock_fluent.return_value.pick_up_tip.assert_called_once()
    args = mock_fluent.return_value.pick_up_tip.call_args[1]
    assert "x" in args
    assert "y" in args
    assert "z" in args

@pytest.mark.asyncio
async def test_aspirate_dispense(mock_fluent, liquid_handler):
    """Test aspirating and dispensing."""
    plate = Plate(
        name="plate",
        size_x=127.76,
        size_y=85.48,
        size_z=14.0,
        model="Tecan 96 Well Plate"
    )
    liquid_handler.deck.assign_child_resource(
        plate,
        location=Coordinate(x=200, y=100, z=100)
    )

    await liquid_handler.setup()
    await liquid_handler.aspirate(
        resource=plate["A1"],
        volume=100,
        flow_rate=100,
        liquid_height=1.0,
        blow_out=True
    )

    mock_fluent.return_value.aspirate.assert_called_once()
    args = mock_fluent.return_value.aspirate.call_args[1]
    assert args["volume"] == 100
    assert args["flow_rate"] == 100
    assert args["liquid_height"] == 1.0
    assert args["blow_out"] is True

    await liquid_handler.dispense(
        resource=plate["B1"],
        volume=100,
        flow_rate=100,
        liquid_height=1.0,
        blow_out=True
    )

    mock_fluent.return_value.dispense.assert_called_once()
    args = mock_fluent.return_value.dispense.call_args[1]
    assert args["volume"] == 100
    assert args["flow_rate"] == 100
    assert args["liquid_height"] == 1.0
    assert args["blow_out"] is True

@pytest.mark.asyncio
async def test_resource_operations(mock_fluent, liquid_handler):
    """Test resource operations (pick up, move, drop)."""
    resource = Resource(
        name="resource",
        size_x=100,
        size_y=100,
        size_z=100
    )
    liquid_handler.deck.assign_child_resource(
        resource,
        location=Coordinate(x=300, y=100, z=100)
    )

    await liquid_handler.setup()
    await liquid_handler.pick_up_resource(resource)
    mock_fluent.return_value.pick_up_labware.assert_called_once()

    await liquid_handler.move_resource(resource, Coordinate(x=400, y=100, z=100))
    mock_fluent.return_value.move_labware.assert_called_once()

    await liquid_handler.drop_resource(resource)
    mock_fluent.return_value.place_labware.assert_called_once()