import pytest
from unittest.mock import AsyncMock
from app.core.websocket import ConnectionManager

@pytest.mark.asyncio
async def test_websocket_manager_connect_disconnect():
    manager = ConnectionManager()
    mock_ws = AsyncMock()
    user_id = 1

    # Test connect
    await manager.connect(mock_ws, user_id)
    assert user_id in manager.active_connections
    assert mock_ws in manager.active_connections[user_id]
    mock_ws.accept.assert_called_once()

    # Test disconnect
    manager.disconnect(mock_ws, user_id)
    assert user_id not in manager.active_connections

@pytest.mark.asyncio
async def test_websocket_manager_messages():
    manager = ConnectionManager()
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    user1 = 1
    user2 = 2

    await manager.connect(ws1, user1)
    await manager.connect(ws2, user2)

    # Personal message
    msg = {"type": "TEST", "content": "hello"}
    await manager.send_personal_message(msg, user1)
    ws1.send_json.assert_called_with(msg)
    ws2.send_json.assert_not_called()

    # Broadcast
    broadcast_msg = {"type": "ALERT", "content": "all"}
    await manager.broadcast(broadcast_msg)
    ws1.send_json.assert_called_with(broadcast_msg)
    ws2.send_json.assert_called_with(broadcast_msg)
