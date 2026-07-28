import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any
from utils import logger


def load_json(path: str | Path, default: dict[str, Any]) -> dict[str, Any]:
    path = Path(path)

    if not path.exists():
        return deepcopy(default)

    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid json file {path}, reinitializing: {e}")
        return deepcopy(default)
    except OSError as e:
        logger.warning(f"Failed to read json file {path}, reinitializing: {e}")
        return deepcopy(default)

    if not isinstance(data, dict):
        logger.warning(f"Invalid json root in {path}, reinitializing")
        return deepcopy(default)

    return data


def save_json(path: str | Path, data: dict[str, Any]) -> None:
    path = Path(path)
    os.makedirs(path.parent, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
