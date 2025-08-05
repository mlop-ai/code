import os

import docker
from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException
from python.docker import start_server, stop_all, stop_server

load_dotenv()

client = docker.from_env()
host = os.getenv("HOST", "localhost")

app = FastAPI()


@app.post("/api/docker/start")
async def _docker_start():
    port, password, url, private_key, ssh_port = start_server(client, host=host)

    cmd_save = f"echo -e '{private_key}' > id_ed25519; chmod 600 id_ed25519"
    cmd_connect = f"{cmd_save}; ssh -i id_ed25519 -p {ssh_port} mlop@{host}"
    cmd_ssh = f"{cmd_save}; echo -e '\nHost {password}\n  HostName {host}\n  Port {ssh_port}\n  User mlop\n  IdentityFile' $(realpath id_ed25519) >> ~/.ssh/config"
    cmd_code = f"{cmd_ssh}; code --remote ssh-remote+{password} /home/mlop"
    return {
        "port": port,
        "password": password,
        "url": url,
        "ssh": cmd_connect,
        "code": cmd_code,
    }  # "key": private_key


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
