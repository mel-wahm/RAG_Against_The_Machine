from src.models import MinimalSource
from src.chunker import Chunker
from pathlib import Path

PUNCTUATION = (
    '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-',
    '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^',
    '`', '{', '|', '}', '~'
)

PYTHON_STOPWORDS = (
    "self", "cls"
)

TEXT_STOPWORDS = (
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
)


class Indexer:
    def __init__(self, chunks: list[MinimalSource]) -> None:
        self.chunks = chunks
        self.content = self.read_chunks("data/raw")
        self.index = self.indexing()

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

    def tokenizer(self, text: str, file_name: str = "") -> list[str]:
        # text_with_camel_case
        stopwords = PYTHON_STOPWORDS if file_name.endswith(".py") \
            else TEXT_STOPWORDS
        for punc in PUNCTUATION:
            text = text.replace(punc, " ")
        result = [t for t in text.split() if t not in stopwords]
        new = []
        for token in result:
            if "_" in token:
                new.extend(map(lambda x: x.lower(), token.split("_")))
        return list(map(lambda x: x.lower(),result)) + [piece for piece in new if piece]

    def indexing(self) -> dict[str, dict[int, int]]:
        index: dict[str, dict[int, int]] = {}
        for num, chunk in enumerate(self.chunks):
            for word in self.tokenizer(self.content[chunk.file_path]
                                       [chunk.first_character_index:
                                       chunk.last_character_index],
                                       chunk.file_path):
                if word in index:
                    if num in index[word]:
                        index[word][num] += 1
                    else:
                        index[word][num] = 1
                else:
                    index[word] = {num: 1}
        return index


indexer = Indexer(Chunker(2000, "data/raw").chunks)
index = indexer.index
