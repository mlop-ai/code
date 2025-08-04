import os
from datetime import datetime, timezone
from typing import Union

import docker
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, Header, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from python.env import get_smtp_config
from python.docker import start_server, stop_server, stop_all

load_dotenv()

SMTP_CONFIG = get_smtp_config()
client = docker.from_env()

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/docker/start")
async def start_docker():
    host = os.getenv('D_DOMAIN', 'localhost')
    port, password, url, private_key, ssh_port = start_server(client, host=host)

    cmd_save = f"echo -e '{private_key}' > id_ed25519; chmod 600 id_ed25519"
    cmd_connect = f"{cmd_save}; ssh -i id_ed25519 -p {ssh_port} mlop@{host}"
    cmd_ssh = f"{cmd_save}; echo -e '\nHost {password}\n  HostName {host}\n  Port {ssh_port}\n  User mlop\n  IdentityFile' $(realpath id_ed25519) >> ~/.ssh/config"
    cmd_code = f"{cmd_ssh}; code --remote ssh-remote+{password} /home/mlop"
    return {"port": port, "password": password, "url": url, "connect": cmd_connect, "code": cmd_code}  # "key": private_key


@app.post("/api/docker/stop")
async def stop_docker(
    port: int = Body(..., embed=True),
):
    try:
        stop_server(client, int(port))
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to stop server: {e}")


@app.post("/api/docker/stop-all")
async def stop_all_docker():
    try:
        stop_all(client)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to stop all servers: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=65526)
