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
        self.index_vector = self.embedding()

    def search(self, query: str, k: int) -> list[int]:
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
        try:
            with open("data/processed/vectors.npy", "rb") as f:
                index_vector = np.load(f)
        except Exception as e:
            print(e, "\n\n")
            for chunk in tqdm(self.index.chunks,
                              desc="Embedding the chunks..."):
                index_vector.append(self.model.encode(
                    self.index.content[chunk.file_path]
                    [chunk.first_character_index:
                     chunk.last_character_index],
                    normalize_embeddings=True
                ))
            with open("data/processed/vectors.npy", "wb") as f:
                np.save(f, index_vector)

        return (index_vector)


if __name__ == "__main__":
    emb = Embedder()
    emb.embedding()
