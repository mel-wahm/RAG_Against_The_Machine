from src.chunker import Chunker
from src.models import MinimalSource

# print("-----------------------------------------")
# print("-----------  HELLO  FROM  RAG -----------")
# print("-----------------------------------------")
# print()
# print()

chunk = Chunker()
chunks: list[MinimalSource] = chunk.chunks
