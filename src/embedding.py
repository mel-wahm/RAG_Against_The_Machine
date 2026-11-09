import pickle
from tqdm import tqdm
import numpy as np
from src.indexer import Indexer


class Embedder:
    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        with open("data/processed/index.pkl", "rb") as f:
            self.index: Indexer = pickle.load(f)
        try:
            with open("data/processed/vectors.npy", "rb") as f:
                self.index_vector = np.load(f)
        except Exception:
            self.index_vector = None

    def search(self, query: str, k: int) -> list[int]:
        if self.index_vector is None:
            raise ValueError("Error: Embedding vectors not found, run the indexer first")
        scores = {}
        query_emb = self.model.encode(query, normalize_embeddings=True)
        for idx, vector in enumerate(self.index_vector):
            scores[idx] = query_emb @ vector
        return sorted(
             scores,
             key=lambda x: scores[x],
             reverse=True
        )[:k]

    def embedding(self) -> list[np.typing.NDArray]:
        index_vector = []
        for chunk in tqdm(self.index.chunks,
                          desc="Embedding the chunks...",
                          colour="GREEN"):
            index_vector.append(self.model.encode(
                self.index.content[chunk.file_path]
                [chunk.first_character_index:
                    chunk.last_character_index],
                normalize_embeddings=True
            ))

        return (index_vector)



