from src.chunker import Chunker
from src.models import MinimalSource

# print("-----------------------------------------")
# print("-----------  HELLO  FROM  RAG -----------")
# print("-----------------------------------------")
# print()
# print()

chunk = Chunker()
# di = []
chunks: list[MinimalSource] = chunk.chunks
for i in chunks:
    length = i.last_character_index - i.first_character_index
    # if length > 2000:
        # print(i)
# print(*di, sep='\n')
