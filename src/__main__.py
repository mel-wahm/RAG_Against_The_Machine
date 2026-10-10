from src.chunker import Chunker
# from src.models import MinimalSource
chunk = Chunker(2000, "data/raw")

ext = [ch for ch in chunk.chunks if ch.last_character_index - ch.first_character_index
        > 2000]
small = [ch for ch in chunk.chunks if ch.last_character_index - ch.first_character_index < 250]
good = [ch for ch in chunk.chunks if 1800 <= ch.last_character_index - ch.first_character_index <= 2000]
# for ch in chunk.chunks:
#     print(ch, ch.last_character_index - ch.first_character_index)

print("safe chunks (under 2000):  -->", len(chunk.chunks) - len(ext), f"({round((len(chunk.chunks) - len(ext)) * 100 / len(chunk.chunks), 2)}%)")
print("small chunks (under 250):   -->", len(small), f"({round(len(small) * 100 / len(chunk.chunks), 2)}%)")
print("big chunks (over 2000):    -->", len(ext))
print("good chunks (over 800, below 2000):    -->", len(good), f"({round(len(good) * 100 / len(chunk.chunks), 2)}%)")
print("total number of chunks:    -->", len(chunk.chunks))

total = 0
for ch in chunk.chunks:
	total += ch.last_character_index - ch.first_character_index

print()
print()
print("Average length of chunks:  -->", round(total / len(chunk.chunks), 2))