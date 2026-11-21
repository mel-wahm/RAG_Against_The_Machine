from pathlib import Path
from src.retriever import Retriever
from src.chunker import Chunker
from src.indexer import Indexer
from src.generator import LLM
from src.evaluator import Evaluator
from src.embedding import Embedder
from src.utils import load_index_and_embeddings, save_pickle, validate_k


class RAG:
    """
    Orchestrate the retrieval-augmented generation pipeline.
    Attributes
    ----------
    data_file : str
        Path to the directory containing the raw data.
    """
    def __init__(self, data_file: str = "data/raw") -> None:
        """
        Initialize the RAG pipeline.
        Parameters
        ----------
        data_file : str, default="data/raw"
            Path to the directory containing the raw data.
        """
        self.data_file = data_file

    def index(self, max_chunk_size: int = 2000) -> None:
        """
        Builds and saves the index and document embeddings.
        Parameters
        ----------
        max_chunk_size : int, default=2000
            Maximum number of characters allowed per chunk.
            Must be between 200 and 2000.

        Returns
        -------
        None
        """
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
        if not Path(self.data_file).exists():
            print(f"Error: Raw data directory '{self.data_file}' not found.")
            return

        try:
            chunks = Chunker(size, self.data_file).chunks

            index = Indexer(chunks, self.data_file)
            save_pickle(Path("data/processed/index.pkl"), index)

            embedder = Embedder(index)
            index_vector = embedder.embedding()
            save_pickle(Path("data/processed/embedding.pkl"), index_vector)
            print("Ingestion complete! Indices saved under data/processed/")
        except Exception as e:
            print(f"Error during indexing: {e}")
            return

    def search(self, query: str = "", k: int = 5) -> None:
        """
        Retrieves and displays the most relevant chunks for a query.

        Parameters
        ----------
        query : str, default=""
            Text query used to search the indexed documents.
        k : int, default=5
            Maximum number of relevant chunks to retrieve.
        
        Returns
        -------
        None
        """
        if not str(query).strip():
            print("No query provided.")
            return
        k_val = validate_k(k)
        if k_val is None:
            return
        index, emb = load_index_and_embeddings()
        if index is None or emb is None:
            return
        try:
            retriever = Retriever(index, emb)
            for chunk in retriever.search_query(str(query), k_val):
                print(chunk)
        except Exception as e:
            print(f"Error during search: {e}")

    def search_dataset(
        self, dataset_path: str, k: int = 5, save_directory: str = "output"
    ) -> None:
        """
        Retrieve relevant sources for every question in a dataset.

        Parameters
        ----------
        dataset_path : str
            Path to the JSON file containing the questions.
        k : int, default=5
            Maximum number of sources to retrieve per question.
        save_directory : str, default="output"
            Directory where the search results will be saved.
        
        Returns
        -------
        None
        """
        if not Path(dataset_path).is_file():
            print(f"Error: Dataset file '{dataset_path}' not found.")
            return
        k_val = validate_k(k)
        if k_val is None:
            return
        index, emb = load_index_and_embeddings()
        if index is None or emb is None:
            return
        try:
            Retriever(index, emb).search_dataset(
                dataset_path, save_directory, k_val
            )
        except Exception as e:
            print(f"Error while searching dataset: {e}")
        print("Saved student_search_results to "
              f"{Path(save_directory) / Path(dataset_path).name}")

    def answer(self, query: str = "", k: int = 5) -> None:
        """
        Generate an answer to a query using retrieved context.

        Parameters
        ----------
        query : str, default=""
            Question to be answered.
        k : int, default=5
            Maximum number of relevant chunks to retrieve
            and provide as context to the language model.
        
        Returns
        -------
        None
        """
        if not str(query).strip():
            print("Empty query provided.")
            return
        k_val = validate_k(k)
        if k_val is None:
            return
        index, emb = load_index_and_embeddings()
        if index is None or emb is None:
            return
        try:
            retrieved = Retriever(index, emb).search_query(
                str(query), k_val
            )
            print(LLM().answer_a_question(str(query), retrieved))
        except Exception as e:
            print(f"Error during answer generation: {e}")

    def answer_dataset(
        self, student_search_results_path: str, save_directory: str = "output"
    ) -> None:
        """
        Generate answers for questions using previously retrieved sources.

        Parameters
        ----------
        student_search_results_path : str
            Path to the JSON file containing the search results.
        save_directory : str, default="output"
            Directory where the generated answers will be saved.
        
        Returns
        -------
        None
        """
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
        """
        Evaluate retrieval performance against a ground-truth dataset.

        Parameters
        ----------
        student_search_results_path : str
            Path to the JSON file containing the retrieved sources.
        dataset_path : str
            Path to the ground-truth dataset used for evaluation.
        
        Returns
        -------
        None
        """
        try:
            Evaluator(student_search_results_path, dataset_path).evaluate()
        except Exception as e:
            print(f"Error during evaluation: {e}")
