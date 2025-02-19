import os

import uvicorn
from dotenv import load_dotenv

load_dotenv()


if __name__ == "__main__":
    https = os.getenv("HTTPS", "False").lower() in ("true", "1", "t", "yes")
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 5001))
    ssl_keyfile = os.getenv("SSL_KEYFILE", "./private/cert/localhost-key.pem")
    ssl_certfile = os.getenv("SSL_CERTFILE", "./private/cert/localhost.pem")

    if os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile) and https:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=True,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
        )
    else:
        uvicorn.run("app.main:app", host=host, port=port, reload=True)
