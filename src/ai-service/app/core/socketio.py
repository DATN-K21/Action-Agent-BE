import socketio

sio = socketio.AsyncServer(cors_allowed_origins=[], async_mode="asgi")
sio_asgi = None


def get_socketio_asgi() -> socketio.ASGIApp:
    """Lazy initialization of the Socket.IO ASGI app."""
    global sio_asgi
    if sio_asgi is None:
        sio_asgi = socketio.ASGIApp(sio)
    return sio_asgi


def get_socketio_server() -> socketio.AsyncServer:
    """Return the raw Socket.IO server instance."""
    return sio
