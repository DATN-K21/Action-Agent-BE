"""
Stream control module for managing active streaming connections.

This module provides thread-safe operations for managing streaming session state,
including stop flags and active connection tracking.
"""

import asyncio
from threading import Lock
from typing import Dict

# Thread-safe dictionary to track active streaming connections
# Key: f"{user_id}:{thread_id}", Value: asyncio.Event
active_connections: Dict[str, asyncio.Event] = {}
_connections_lock = Lock()


def create_stop_event(user_id: str, thread_id: str) -> asyncio.Event:
    """
    Create a stop event for a specific user and thread combination.

    Args:
        user_id: The user identifier
        thread_id: The thread identifier

    Returns:
        asyncio.Event: The stop event for this connection
    """
    connection_key = f"{user_id}:{thread_id}"
    stop_event = asyncio.Event()

    with _connections_lock:
        active_connections[connection_key] = stop_event

    return stop_event


def trigger_stop(user_id: str, thread_id: str) -> bool:
    """
    Trigger stop for a specific user and thread combination.

    Args:
        user_id: The user identifier
        thread_id: The thread identifier

    Returns:
        bool: True if the connection was found and stop was triggered, False otherwise
    """
    connection_key = f"{user_id}:{thread_id}"

    with _connections_lock:
        if connection_key in active_connections:
            active_connections[connection_key].set()
            return True

    return False


def cleanup_connection(user_id: str, thread_id: str) -> None:
    """
    Clean up a connection after streaming is complete.

    Args:
        user_id: The user identifier
        thread_id: The thread identifier
    """
    connection_key = f"{user_id}:{thread_id}"

    with _connections_lock:
        if connection_key in active_connections:
            del active_connections[connection_key]


def is_stop_requested(user_id: str, thread_id: str) -> bool:
    """
    Check if stop has been requested for a specific connection.

    Args:
        user_id: The user identifier
        thread_id: The thread identifier

    Returns:
        bool: True if stop was requested, False otherwise
    """
    connection_key = f"{user_id}:{thread_id}"

    with _connections_lock:
        if connection_key in active_connections:
            return active_connections[connection_key].is_set()

    return False


def get_active_connections_count() -> int:
    """
    Get the number of active streaming connections.

    Returns:
        int: Number of active connections
    """
    with _connections_lock:
        return len(active_connections)
