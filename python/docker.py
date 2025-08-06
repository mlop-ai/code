import logging
import os
import random
import socket
import uuid

import docker

from . import traefik, utils

logger = logging.getLogger(__name__)


def start_server(
    client: docker.DockerClient,
    host: str = "localhost",
    port_range: tuple[int, int] = (20000, 40000),
    gpu: bool = False,
):
    port = random.randint(port_range[0], port_range[1])
    while _get_port(port):
        port = random.randint(port_range[0], port_range[1])

    password = uuid.uuid4().hex  # [:8]
    private_key, public_key = utils.gen_ed25519()
    deploy_code(
        client=client,
        project_dir=f"/var/tmp/docker-code-{str(port)}",
        host_port=port,
        password=password,
        image_name="mlop-code-server:latest",
        gpu=gpu,
        authorized_keys=public_key,
        host=host,
    )
    logger.info(f"Started code-server at port {port} with password {password}")
    return (
        port,
        password,
        f"https://mlop:{password}@{host}/{port}/{password}/",
        private_key,
    )


def stop_server(client: docker.DockerClient, port: int):
    traefik.delete_route(port)
    client.containers.get(f"code-{str(port)}").stop()


def stop_all(client: docker.DockerClient):
    containers = client.containers.list(all=True)
    for c in containers:
        if c.name.startswith("code-"):
            try:
                port = int(c.name.split("-")[1])
                traefik.delete_route(port)
            except (IndexError, ValueError):
                pass
            c.stop()


def _get_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
            return False
        except socket.error:
            return True


def deploy_code(
    client: docker.DockerClient,
    project_dir: str,
    host_port: int = 2222,
    password: str = None,
    image_name: str = "mlop-code-server:latest",
    gpu: bool = False,
    authorized_keys: str = "",
    cache_dir: str = os.path.abspath(os.getcwd()),
    host: str = "localhost",
    size: int = 2,
) -> dict:
    try:
        code_container = client.containers.run(
            image_name,
            detach=True,
            auto_remove=True,
            read_only=True,
            tmpfs={
                "/home/mlop": "rw,exec,mode=0775,uid=1000,gid=1000",
                "/home/linuxbrew": "rw,exec,mode=0775,uid=1000,gid=1000",
                "/tmp": ""
            },
            cap_drop=["all"],
            security_opt=["no-new-privileges"],
            mem_limit=f"{str(size)}g",
            nano_cpus=int(size * 1_000_000_000),
            name=f"code-{str(host_port)}",
            network="traefik",
            command="--disable-telemetry --auth none",
            environment={
                "AUTHORIZED_KEYS": authorized_keys,
                # "PASSWORD": password
            },
            ports={
                "2222/tcp": host_port,
            },
            # volumes={os.path.abspath(project_dir): {"bind": "/home/mlop/project", "mode": "rw"}},
            # tty=True, stdin_open=True,
            cpu_count=4,
            **(
                {
                    "device_requests": [
                        docker.types.DeviceRequest(
                            device_ids=["all"], capabilities=[["gpu"]]
                        )  # ['0', '2']
                    ]
                }
                if gpu
                else {}
            ),
        )
        traefik.add_route(host_port, password, host)

        return f"{host_port}", code_container
    except Exception as e:
        logger.error(f"Error starting containers: {e}")
        return None
