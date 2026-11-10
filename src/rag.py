from typing import Callable, Any
from pathlib import Path
import pickle
from src.retriever import Retriever
from src.chunker import Chunker
from src.indexer import Indexer
from src.generator import LLM
from src.evaluator import Evaluator
from src.embedding import Embedder


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
    def __init__(self, data_file: str = "data/raw") -> None:
        self.data_file = data_file

    def index(self, max_chunk_size: int = 2000) -> None:
        try:
            size = int(max_chunk_size)
        except (ValueError, TypeError):
            print("Error: max_chunk_size must be an integer.")
            return
        if size <= 0:
            print("Error: max_chunk_size must be a positive integer.")
            return
        if not 400 <= size <= 2000:
            print("Error: max_chunk_size must be a between 400 and 2000.")
            return
        if not Path(self.data_file).exists():
            print(f"Error: Raw data directory '{self.data_file}' not found.")
            return
        Path("data/processed").mkdir(parents=True, exist_ok=True)

        chunks_path = Path("data/processed/chunks.pkl")
        chunks = Chunker(size, self.data_file).chunks
        temp_chunks = chunks_path.with_suffix(".tmp")
        with open(temp_chunks, "wb") as f:
            pickle.dump(chunks, f)
        temp_chunks.replace(chunks_path)

        index_path = Path("data/processed/index.pkl")
        index = Indexer(chunks, self.data_file)
        temp_index = index_path.with_suffix(".tmp")
        with open(temp_index, "wb") as f:
            pickle.dump(index, f)
        temp_index.replace(index_path)

        Embedder()

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
        chunks = load_or_build(
            Path("data/processed/chunks.pkl"),
            lambda: Chunker(2000, self.data_file).chunks,
        )
        index = load_or_build(
            Path("data/processed/index.pkl"),
            lambda: Indexer(chunks, self.data_file),
        )
        try:
            retrieved = Retriever(index).search_query(str(query), k_val)
            for chunk in retrieved:
                print(chunk)
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
            print(f"Error: Invalid value for k: '{k}'. Must be an integer.")
            return
        if k_val <= 0:
            print(f"Error: k must be greater than 0 (received k={k_val}).")
            return
        chunks = load_or_build(
            Path("data/processed/chunks.pkl"),
            lambda: Chunker(2000, self.data_file).chunks,
        )
        index = load_or_build(
            Path("data/processed/index.pkl"),
            lambda: Indexer(chunks, self.data_file),
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
            print(f"Error: k must be greater than 0 (received k={k_val}).")
            return
        chunks = load_or_build(
            Path("data/processed/chunks.pkl"),
            lambda: Chunker(2000, self.data_file).chunks,
        )
        index = load_or_build(
            Path("data/processed/index.pkl"),
            lambda: Indexer(chunks, self.data_file),
        )
        try:
            retriever = Retriever(index)
            retrieved_chunks = retriever.search_query(str(query), k_val)
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
