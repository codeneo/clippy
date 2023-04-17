import json
from dataclasses import dataclass


@dataclass
class RedisConfig:
    local_url: str
    remote_url: str
    channel: str

    @classmethod
    def from_dict(cls, data):
        return cls(
            local_url=data.get("local_url"),
            remote_url=data.get("remote_url"),
            channel=data.get("channel")
        )


@dataclass
class CipherConfig:
    enabled: bool
    key: str

    @classmethod
    def from_dict(cls, data):
        return cls(
            enabled=data.get("enabled"),
            key=data.get("key")
        )


@dataclass
class ApplicationConfig:
    redis: RedisConfig
    cipher: CipherConfig

    @classmethod
    def from_json(cls, path):
        with open(path, 'r') as f:
            data = json.load(f)
            return cls(
                redis=RedisConfig.from_dict(data.get("redis")),
                cipher=CipherConfig.from_dict(data.get("cipher"))
            )


def main():
    application_config = ApplicationConfig.from_json('config.json')
    print(f"{application_config=}")


if __name__ == '__main__':
    print(f"Executing submodule [{__file__}] as a script.")
    main()

