import numpy as np

class Embedder:
    def __init__(self, index) -> None:
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = index

    def embedding(self) -> np.ndarray:
        texts = []
        for chunk in self.index.chunks:
            try:
                source = self.index.content[chunk.file_path][
                    chunk.first_character_index: chunk.last_character_index
                ]
            except Exception:
                source = ""
            texts.append(source)
        index_vector = self.model.encode(
            texts,
            batch_size=16,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        return index_vector
