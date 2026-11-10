from pathlib import Path
import torch
import pickle
import numpy as np
from src.indexer import Indexer


class Embedder:
    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        torch.set_num_threads(8)
        with open("data/processed/index.pkl", "rb") as f:
            self.index: Indexer = pickle.load(f)
        from src.rag import load_or_build
        self.index_vector = load_or_build(Path("data/processed/vectors.pkl"),
                                          lambda: self.embedding())

    def search(self, query: str, k: int) -> list[int]:
        query_emb = self.model.encode(query, normalize_embeddings=True)
        scores = self.index_vector @ query_emb
        top_k: list[int] = np.argsort(-scores)[:k].tolist()
        return top_k

    def embedding(self) -> np.ndarray:
        texts = [
            self.index.content[chunk.file_path][
                chunk.first_character_index: chunk.last_character_index
            ]
            for chunk in self.index.chunks
        ]
        index_vector = self.model.encode(
            texts,
            batch_size=16,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        return index_vector
