from src.retriever import Retriever
from src.chunker import Chunker
from src.indexer import Indexer
from typing import Callable, Any
import fire
import pickle
from pathlib import Path


def load_or_build(path: Path, build: Callable) -> Any:
    try:
        with open(path, "rb") as f:
            obj = pickle.load(f)
        print(f"Loaded {path.name} from disk")
        return obj
    except (FileNotFoundError, PermissionError):
        print(f"{path.name} not found. Building..")
        obj = build()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(obj, f)
        return obj


class RAG():
    def __init__(self) -> None:
        pass

    def index(self, max_chunk_size=1600) -> None:
        chunks = load_or_build(Path("data/processed/chunks.pkl"),
                               lambda: Chunker(max_chunk_size, "data/raw").chunks)
        index = load_or_build(Path("data/processed/index.pkl"),
                              lambda: Indexer(chunks))
        assert type(index) is Indexer

    def search(self, query, k=5):
        try:
            with open("data/processed/index.pkl", "rb") as f:
                index : Indexer = pickle.load(f)
            scores = index.bm25(query, k)
            for score in scores:
                chunk = index.chunks[score[0]]
                print(f"{chunk.file_path}, "
                    f"[{chunk.first_character_index}:"
                    f"{chunk.last_character_index}] "
                    f"score: {score[1]:.3f}")
        except Exception:
            raise Exception("No indeces available, please run \"uv run -m "
                            "src index --max_chunk_size=<int>\" first")

    def search_dataset(self, dataset_path: str, k: int,
                       save_directory: str) -> None:
        if k > 15:
            raise ValueError("K must be between 1 and 15")
        try:
            with open("data/processed/index.pkl", "rb") as f:
                index = pickle.load(f)
            Retriever(index).answer_dataset(dataset_path, save_directory, k)
        except Exception:
            raise Exception("No indeces available, please run \"uv run -m "
                            "src index --max_chunk_size=<int>\" first")

fire.Fire(
    RAG
)