from pathlib import Path
from src.retriever import Retriever
from src.chunker import Chunker
from src.indexer import Indexer
from src.generator import LLM
from src.evaluator import Evaluator
from src.embedding import Embedder
from src.utils import load_or_build, save_atomic, validate_k


class RAG:
    def __init__(self, data_file: str = "data/raw") -> None:
        self.data_file = data_file

    def _get_index(self) -> Indexer:
        chunks = load_or_build(
            Path("data/processed/chunks.pkl"),
            lambda: Chunker(2000, self.data_file).chunks,
        )
        index: Indexer = load_or_build(
            Path("data/processed/index.pkl"),
            lambda: Indexer(chunks, self.data_file),
        )
        return index

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

        # Catch build and validation errors gracefully to prevent CLI crashes
        try:
            chunks = Chunker(size, self.data_file).chunks
            save_atomic(Path("data/processed/chunks.pkl"), chunks)

            index = Indexer(chunks, self.data_file)
            save_atomic(Path("data/processed/index.pkl"), index)

            embedder = Embedder(index)
            index_vector = embedder.embedding()
            save_atomic(Path("data/processed/vectors.pkl"), index_vector)
        except Exception as e:
            print(f"Error during indexing: {e}")
            return

    def search(self, query: str = "", k: int = 5) -> None:
        if not str(query).strip():
            return
        k_val = validate_k(k)
        if k_val is None:
            return
        try:
            retriever = Retriever(self._get_index())
            for chunk in retriever.search_query(str(query), k_val):
                print(chunk)
        except Exception as e:
            print(f"Error during search: {e}")

    def search_dataset(
        self, dataset_path: str, k: int = 5, save_directory: str = "output"
    ) -> None:
        if not Path(dataset_path).is_file():
            print(f"Error: Dataset file '{dataset_path}' not found.")
            return
        k_val = validate_k(k)
        if k_val is None:
            return
        Retriever(self._get_index()).search_dataset(
            dataset_path, save_directory, k_val
        )

    def answer(self, query: str = "", k: int = 1) -> None:
        if not str(query).strip():
            print("Warning: Empty query provided.")
            return
        k_val = validate_k(k)
        if k_val is None:
            return
        try:
            retrieved = Retriever(self._get_index()).search_query(
                str(query), k_val
            )
            print(LLM().answer_a_question(str(query), retrieved))
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
        # Catch evaluation errors gracefully without crashing the CLI
        try:
            Evaluator(student_search_results_path, dataset_path).evaluate()
        except Exception as e:
            print(f"Error during evaluation: {e}")
