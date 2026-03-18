# lagrange/info/serialize.py

import json
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class DeviceInfo:
    model: str
    os: str
    version: str
    display: Optional[str] = None  # 可选字段

    @classmethod
    def load(cls, buffer: str):
        """
        从 JSON 加载 DeviceInfo，忽略多余字段
        """
        data = json.loads(buffer)
        valid_keys = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

    def dump(self) -> str:
        """
        序列化为 JSON
        """
        return json.dumps(self.__dict__)


class JsonSerializer:
    @staticmethod
    def dumps(obj: Any) -> str:
        return json.dumps(obj)

    @staticmethod
    def loads(s: str) -> Any:
        return json.loads(s)


class BinarySerializer:
    @staticmethod
    def dumps(obj: Any) -> bytes:
        return json.dumps(obj).encode("utf-8")

    @staticmethod
    def loads(b: bytes) -> Any:
        return json.loads(b.decode("utf-8"))