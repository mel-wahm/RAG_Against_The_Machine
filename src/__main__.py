import sys
from typing import Callable, Any
from pathlib import Path
import pickle
import fire
from src.retriever import Retriever
from src.chunker import Chunker
from src.indexer import Indexer
from src.generator import LLM
from src.evaluator import Evaluator


def load_or_build(path: Path, build: Callable) -> Any:
    try:
        with open(path, "rb") as f:
            obj = pickle.load(f)
        print(f"Loaded {path.name} from disk")
        return obj
    except (
        FileNotFoundError,
        PermissionError,
        Exception
    ):
        print(f"{path.name} not found or incomplete. Building..")
        try:
            obj = build()
            path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = path.with_suffix(".tmp")
            with open(temp_path, "wb") as f:
                pickle.dump(obj, f)
            temp_path.replace(path)
            return obj
        except Exception as e:
            print(f"Error building {path.name}: {e}")
            raise SystemExit(1)


class RAG:
    def __init__(self) -> None:
        pass

    def index(self, max_chunk_size: int = 1600) -> None:
        try:
            size = int(max_chunk_size)
        except (ValueError, TypeError):
            print("Error: max_chunk_size must be an integer.")
            return
        if size <= 0:
            print("Error: max_chunk_size must be a positive integer.")
            return
        if not 200 <= size <= 2000:
            print("Error: max_chunk_size must be a between 200 and 2000.")
            return
        if not Path("data/raw").exists():
            print("Error: Raw data directory 'data/raw' not found.")
            return
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        try:
            chunks_path = Path("data/processed/chunks.pkl")
            chunks = Chunker(size, "data/raw").chunks
            temp_chunks = chunks_path.with_suffix(".tmp")
            with open(temp_chunks, "wb") as f:
                pickle.dump(chunks, f)
            temp_chunks.replace(chunks_path)

            index_path = Path("data/processed/index.pkl")
            index = Indexer(chunks)
            temp_index = index_path.with_suffix(".tmp")
            with open(temp_index, "wb") as f:
                pickle.dump(index, f)
            temp_index.replace(index_path)
        except Exception as e:
            print(f"Error creating index: {e}")

    def search(self, query: str = "", k: int = 5) -> None:
        if not str(query).strip():
            return
        try:
            k_val = int(k)
        except (ValueError, TypeError):
            print(f"Error: Invalid value for k: '{k}'. Must be an integer.")
            return
        if k_val <= 0:
            return
        index_path = Path("data/processed/index.pkl")
        if not index_path.exists():
            print(
                "Error: Index not found. Please run 'uv run python -m "
                "src index --max_chunk_size=<int>' first."
            )
            return
        try:
            with open(index_path, "rb") as f:
                index: Indexer = pickle.load(f)
            scores = index.bm25(str(query), k_val)
            for score in scores:
                chunk = index.chunks[score[0]]
                print(
                    f"{chunk.file_path}, "
                    f"[{chunk.first_character_index}:"
                    f"{chunk.last_character_index}] "
                    f"score: {score[1]:.3f}"
                )
        except Exception as e:
            print(f"Error during search: {e}")

    def search_dataset(
        self, dataset_path: str, k: int = 5, save_directory: str = "output"
    ) -> None:
        if not Path(dataset_path).is_file():
            print(f"Error: Dataset file '{dataset_path}' not found.")
            return
        try:
            k_val = int(k)
        except (ValueError, TypeError):
            try:
                k_val = int(save_directory)
                save_directory = str(k)
            except (ValueError, TypeError):
                print(
                    f"Error: Invalid value for k: '{k}'. Must be an integer."
                )
                return
        if k_val <= 0:
            print(f"Warning: k must be greater than 0 (received k={k_val}).")
            return
        chunks = load_or_build(
            Path("data/processed/chunks.pkl"),
            lambda: Chunker(1600, "data/raw").chunks,
        )
        index = load_or_build(
            Path("data/processed/index.pkl"), lambda: Indexer(chunks)
        )
        Retriever(index).search_dataset(dataset_path, save_directory, k_val)

    def answer(self, query: str = "", k: int = 1) -> None:
        if not str(query).strip():
            print("Warning: Empty query provided.")
            return
        try:
            k_val = int(k)
        except (ValueError, TypeError):
            print(f"Error: Invalid value for k: '{k}'. Must be an integer.")
            return
        if k_val <= 0:
            print(f"Warning: k must be greater than 0 (received k={k_val}).")
            return
        chunks = load_or_build(
            Path("data/processed/chunks.pkl"),
            lambda: Chunker(1600, "data/raw").chunks,
        )
        index = load_or_build(
            Path("data/processed/index.pkl"), lambda: Indexer(chunks)
        )
        scores = index.bm25(str(query), k_val)
        retrieved_chunks = [index.chunks[score] for score, _ in scores]
        try:
            model = LLM()
            full_prompt = model.prepare_prompt(str(query), retrieved_chunks)
            print(model.answer_a_question(full_prompt))
        except Exception as e:
            print(f"Error during answer generation: {e}")

    def answer_dataset(
        self, student_search_results_path: str, save_directory: str = "output"
    ) -> None:
        if not Path(student_search_results_path).is_file():
            print(f"Error: File '{student_search_results_path}' not found.")
            return
        try:
            LLM().answer_dataset(student_search_results_path, save_directory)
        except Exception as e:
            print(f"Error during answer_dataset: {e}")

    def evaluate(
        self, student_search_results_path: str, dataset_path: str
    ) -> None:
        Evaluator(student_search_results_path, dataset_path).evaluate()


if __name__ == "__main__":
    try:
        fire.Fire(RAG)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", flush=True)
        sys.exit(130)
    except Exception as e:
        print(e)
