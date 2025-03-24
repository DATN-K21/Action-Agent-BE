import socketio

# Create a shared Socket.IO server instance
sio_asgi = socketio.AsyncServer(async_mode="asgi")
