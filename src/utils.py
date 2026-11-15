from src.indexer import Indexer
from src.chunker import Chunker

from pathlib import Path
from typing import Callable, Any
import pickle


def save_pickle(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    with open(temp_path, "wb") as f:
        pickle.dump(obj, f)
    temp_path.replace(path)


def load_or_build(path: Path, build: Callable) -> Any:
    try:
        with open(path, "rb") as f:
            obj = pickle.load(f)
        print(f"Loaded {path.name} from disk")
        return obj
    except (FileNotFoundError, PermissionError, Exception):
        print(f"{path.name} not found or incomplete. Building..")
        try:
            obj = build()
            save_pickle(path, obj)
            return obj
        except Exception as e:
            print(f"Error building {path.name}: {e}")
            raise SystemExit(1)


def validate_k(k: Any) -> int | None:
    if isinstance(k, bool):
        print(f"Error: Invalid value for k: '{k}'. Must be an integer.")
        return None
    try:
        k_val = int(k)
    except (ValueError, TypeError):
        print(f"Error: Invalid value for k: '{k}'. Must be an integer.")
        return None
    if k_val <= 0:
        print(f"Error: k must be greater than 0 (received k={k_val}).")
        return None
    return k_val


def get_index(data_file: str) -> Indexer:
    chunks = load_or_build(
        Path("data/processed/chunks.pkl"),
        lambda: Chunker(2000, data_file).chunks,
    )
    index: Indexer = load_or_build(
        Path("data/processed/index.pkl"),
        lambda: Indexer(chunks, data_file),
    )
    return index
