from src.models import MinimalSource
from src.chunker import Chunker
from pathlib import Path
import re
from math import log
from heapq import nlargest
from collections import defaultdict

query = "self"

PUNCTUATION = {
    '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-',
    '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^',
    '`', '{', '|', '}', '~'
}

PYTHON_STOPWORDS = {
    "self", "cls"
}

TEXT_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "nor",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had",
    "i", "me", "my", "we", "our", "you", "your", "he", "she",
    "it", "they", "them",
    "this", "that", "these", "those",
    "of", "at", "by", "for", "from", "in", "into", "on", "onto",
    "to", "with", "without",
    "as", "if", "then", "than", "because", "while", "when", "where",
    "can", "could", "may", "might", "must", "shall", "should",
    "will", "would",
    "not", "no", "so", "very", "just", "also", "only", "each",
    "all", "any", "some"
    }


class Indexer:
    def __init__(self, chunks: list[MinimalSource],
                 k: float = 1.2, b: float = 0.8) -> None:
        self.chunks = chunks
        self.k = k
        self.b = b
        self.content = self.read_chunks("data/raw")
        self.chunks_length: list[int] = []
        self.index = self.indexing()
        self.chunks_average_length = sum(self.chunks_length) / len(self.chunks)
        self.penalty = []
        for length in self.chunks_length:
            self.penalty.append(k * (1 - b + b * (length /
                                                  self.chunks_average_length)))

    def read_chunks(self, folder_path: str) -> dict[str, str]:
        files = [str(file) for file in Path(folder_path).rglob("*")
                 if any(str(file).endswith(prefix)
                        for prefix in (".py", ".txt", ".md"))]
        content: dict[str, str] = {}
        for file in files:
            try:
                with open(file) as f:
                    source = f.read()
            except Exception:
                continue
            content[file] = source
        return content

    def split_camel(self, text: str) -> list[str]:
        text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
        text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text)
        return list(map(lambda x: x.lower(), text.split()))

    def calculate_idf(self, token: str) -> float:
        n = len(self.chunks)
        nt = len(self.index.get(token, {}))
        scores = log(1 + (n - nt + 0.5) / (nt + 0.5))
        return scores

    def bm25(self, query: str, top_k: int) -> list[tuple[int, float]]:
        scores = defaultdict(float)
        k = self.k
        for token in self.tokenizer(query):
            if token not in self.index:
                continue
            multiplier = 1.4 if "_" in token else 1
            idf = self.calculate_idf(token)
            for chunk, tf in self.index[token].items():
                bast = tf * (k + 1)
                maqam = tf + self.penalty[chunk]
                scores[chunk] += idf * (bast / maqam) * multiplier
        new_scores = nlargest(top_k, scores.items(), key=lambda elem: elem[1])
        return new_scores

    def tokenizer(self, text: str, file_name: str = "") -> list[str]:
        if file_name:
            stopwords = PYTHON_STOPWORDS if file_name.endswith(".py") \
                else TEXT_STOPWORDS
        else:
            stopwords = TEXT_STOPWORDS
        for punc in PUNCTUATION:
            text = text.replace(punc, " ")
        result = [t for t in text.split() if t.lower() not in stopwords
                  and not t.isdigit()]
        new = []
        for token in result:
            res = self.split_camel(token)
            if len(res) > 1:
                new.extend(res)
            if "_" in token:
                new.extend(map(lambda x: x.lower(), token.split("_")))
        return list(map(lambda x: x.lower(), result)) + \
            [piece for piece in new if piece and piece not in stopwords]

    def indexing(self) -> dict[str, dict[int, int]]:
        index: dict[str, dict[int, int]] = {}
        for chunk_number, chunk in enumerate(self.chunks):
            tokens = self.tokenizer(self.content[chunk.file_path]
                                    [chunk.first_character_index:
                                    chunk.last_character_index],
                                    chunk.file_path) + self.tokenizer(chunk.file_path)
            for word in tokens:
                if word in index:
                    if chunk_number in index[word]:
                        index[word][chunk_number] += 1
                    else:
                        index[word][chunk_number] = 1
                else:
                    index[word] = {chunk_number: 1}
            self.chunks_length.append(len(tokens))
        return index


if __name__ == "__main__":
    indexer = Indexer(Chunker(2000, "data/raw").chunks)
    query = "What is the default timeout value for vLLM RPC operations?"
    scores = indexer.bm25(query, 5)
    for chunk, score in scores:
        print(indexer.chunks[chunk].file_path)
