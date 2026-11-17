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


def load_or_build(path: Path, build: Callable, silent: bool = False)\
      -> Any:
    try:
        with open(path, "rb") as f:
            obj = pickle.load(f)
        if not silent:
            print(f"Loaded {path.name} from disk")
        return obj
    except (FileNotFoundError, PermissionError, Exception):
        if not silent:
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


def load_index_and_embeddings() -> Any:
    try:
        with open("data/processed/index.pkl", "rb") as f:
            index = pickle.load(f)
    except Exception:
        print("index not found, please run the indexer first")
        return None, None
    try:
        with open("data/processed/embedding.pkl", "rb") as f:
            emb = pickle.load(f)
    except Exception:
        print("embedding vectors not found, please run the indexer first")
        return None, None
    
    return index, emb
