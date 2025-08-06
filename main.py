import logging
import os
from urllib.parse import urlparse

import docker
from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException
from python.docker import start_server, stop_all, stop_server

logger = logging.getLogger(__name__)

load_dotenv()

client = docker.from_env()
host = os.getenv("HOST", "localhost")

app = FastAPI()


@app.post("/api/docker/start")
async def _docker_start(url: str = Body(None, embed=True)):
    try:
        if url:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]) or parsed.scheme not in [
                "http",
                "https",
            ]:
                raise ValueError("Invalid URL")

        port, password, server_url, private_key = start_server(
            client, host=host, url=url
        )
        cmd_save = f"echo -e '{private_key}' > id_ed25519; chmod 600 id_ed25519"
        # cmd_ssh_config = f"{cmd_save}; echo -e '\nHost {password}\n  HostName {host}\n  Port {port}\n  User mlop\n  IdentityFile' $(realpath id_ed25519) >> ~/.ssh/config"
        # cmd_code = f"{cmd_ssh_config}; code --remote ssh-remote+{password} /home/mlop"
        return {
            "port": port,
            "password": password,
            "url": server_url,
            "ssh": f"{cmd_save}; ssh -i id_ed25519 -p {port} mlop@{host}",  # "code": cmd_code,
        }
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise HTTPException(status_code=500, detail="Failed to start server")


@app.post("/api/docker/stop")
async def _docker_stop(
    port: int = Body(..., embed=True),
):
    try:
        stop_server(client, int(port))
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop server: {e}")


@app.post("/api/docker/stop/all")
async def _docker_stop_all():
    try:
        stop_all(client)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop all servers: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=65526)
