from src.retriever import Retriever
from src.chunker import Chunker
from src.indexer import Indexer
from src.generator import LLM
from src.evaluator import Evaluator
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

    def index(self, max_chunk_size: int = 1600) -> None:
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        with open("data/processed/chunks.pkl", "wb") as f:
            chunks = Chunker(max_chunk_size, "data/raw").chunks
            pickle.dump(chunks, f)
        with open("data/processed/index.pkl", "wb") as f:
            index = Indexer(chunks)
            pickle.dump(index, f)

    def search(self, query: str, k: int = 5) -> None:
        try:
            with open("data/processed/index.pkl", "rb") as f:
                index: Indexer = pickle.load(f)
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

    def search_dataset(self, dataset_path: str, k: int = 5,
                       save_directory: str = "output") -> None:
        chunks = load_or_build(Path("data/processed/chunks.pkl"),
                               lambda: Chunker(1600, "data/raw").chunks)
        index = load_or_build(Path("data/processed/index.pkl"),
                              lambda: Indexer(chunks))
        Retriever(index).search_dataset(dataset_path, save_directory, k)

    def answer(self, query: str, k: int = 1) -> None:
        chunks = load_or_build(Path("data/processed/chunks.pkl"),
                               lambda: Chunker(1600, "data/raw").chunks)
        index = load_or_build(Path("data/processed/index.pkl"),
                              lambda: Indexer(chunks))
        scores = index.bm25(query, k)
        retrieved_chunks = [index.chunks[score] for score, _ in scores]
        model = LLM()
        full_prompt = model.prepare_prompt(query, retrieved_chunks)
        print(model.answer_a_question(full_prompt))

    def answer_dataset(
        self, student_search_results_path: str,
        save_directory: str = "output"
    ) -> None:
        LLM().answer_dataset(student_search_results_path, save_directory)

    def evaluate(
        self, student_search_results_path: str,
        dataset_path: str
    ) -> None:
        Evaluator(student_search_results_path, dataset_path).evaluate()


fire.Fire(
    RAG
)
