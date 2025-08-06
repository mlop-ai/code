import os

import bcrypt
import yaml


def load_config():
    config_file = "traefik/dynamic/routes.yml"
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return yaml.safe_load(f) or {
                "http": {"routers": {}, "services": {}, "middlewares": {}}
            }
    return {"http": {"routers": {}, "services": {}, "middlewares": {}}}


def save_config(config):
    config_file = "traefik/dynamic/routes.yml"
    if not config["http"]["routers"]:
        if os.path.exists(config_file):
            os.remove(config_file)
        return

    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def add_route(port: int, password: str, host: str = "localhost"):
    config = load_config()

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
    save_config(config)


def delete_route(port: int):
    config = load_config()
    config["http"]["routers"].pop(f"code-{port}", None)
    config["http"]["services"].pop(f"code-{port}", None)
    config["http"]["middlewares"].pop(f"strip-{port}", None)
    config["http"]["middlewares"].pop(f"auth-{port}", None)
    save_config(config)
