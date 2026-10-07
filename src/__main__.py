from src.chunker import Chunker
# from src.models import MinimalSource
chunk = Chunker(2000, "data/raw")
ext = [ch for ch in chunk.chunks if ch.last_character_index - ch.first_character_index
        > 2000]
small = [ch for ch in chunk.chunks if ch.last_character_index - ch.first_character_index
        < 100]
# for ch in chunk.chunks:
#     print(ch, ch.last_character_index - ch.first_character_index)

print("safe chunks (under 2000):  -->", len(chunk.chunks) - len(ext), f"({round((len(chunk.chunks) - len(ext)) * 100 / len(chunk.chunks), 2)}%)")
print("small chunks (under 50):   -->", len(small), f"({round(len(small) * 100 / len(chunk.chunks), 2)}%)")
print("big chunks (over 2000):    -->", len(ext))
print("total number of chunks:    -->", len(chunk.chunks))
