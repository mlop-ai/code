import os
import random
import socket
import uuid

import bcrypt
import docker
import yaml

from .utils import gen_ed25519


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
    private_key, public_key = gen_ed25519()
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
    print(f"Started code-server at port {port} with password {password}")
    return (
        port,
        password,
        f"https://mlop:{password}@{host}/{port}/{password}/",
        private_key,
    )


def stop_server(client: docker.DockerClient, port: int):
    _traefik_del_route(port)
    client.containers.get(f"code-{str(port)}").stop()


def stop_all(client: docker.DockerClient):
    containers = client.containers.list(all=True)
    for c in containers:
        if c.name.startswith("code-"):
            try:
                port = int(c.name.split("-")[1])
                _traefik_del_route(port)
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


def _traefik_load():
    config_file = "traefik/dynamic/routes.yml"
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return yaml.safe_load(f) or {
                "http": {"routers": {}, "services": {}, "middlewares": {}}
            }
    return {"http": {"routers": {}, "services": {}, "middlewares": {}}}


def _traefik_save(config):
    config_file = "traefik/dynamic/routes.yml"
    if not config["http"]["routers"]:
        if os.path.exists(config_file):
            os.remove(config_file)
        return

    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def _traefik_add_route(port: int, password: str, host: str = "localhost"):
    config = _traefik_load()

    config["http"]["routers"][f"code-{port}"] = {
        "rule": f"Host(`{host}`) && PathPrefix(`/{port}/{password}/`)",
        "service": f"code-{port}",
        "tls": {"certResolver": "letsencrypt"},
        "middlewares": [f"strip-{port}", f"auth-{port}"],
    }
    config["http"]["services"][f"code-{port}"] = {
        "loadBalancer": {"servers": [{"url": f"http://code-{port}:8080"}]}
    }
    config["http"]["middlewares"][f"strip-{port}"] = {
        "stripPrefix": {"prefixes": [f"/{port}/{password}"]}
    }
    config["http"]["middlewares"][f"auth-{port}"] = {
        "basicAuth": {
            "users": [
                f"mlop:{bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()}"
            ]
        }
    }
    _traefik_save(config)


def _traefik_del_route(port: int):
    config = _traefik_load()
    config["http"]["routers"].pop(f"code-{port}", None)
    config["http"]["services"].pop(f"code-{port}", None)
    config["http"]["middlewares"].pop(f"strip-{port}", None)
    config["http"]["middlewares"].pop(f"auth-{port}", None)
    _traefik_save(config)


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
        _traefik_add_route(host_port, password, host)

        return f"{host_port}", code_container
    except Exception as e:
        print(f"Error starting containers: {e}")
        return None
