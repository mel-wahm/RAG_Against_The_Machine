from src.chunker import Chunker

chunk = Chunker(2000, "data/raw")

ext = [
    ch
    for ch in chunk.chunks
    if ch.last_character_index - ch.first_character_index > 2000
]
small = [
    ch
    for ch in chunk.chunks
    if ch.last_character_index - ch.first_character_index < 250
]
good = [
    ch
    for ch in chunk.chunks
    if 1000 <= ch.last_character_index - ch.first_character_index <= 2000
]

if not len(chunk.chunks):
    print(f"total number of chunks:    --> {len(chunk.chunks)}")
    exit()
safe_count = len(chunk.chunks) - len(ext)
safe_pct = round(safe_count * 100 / len(chunk.chunks), 2)
small_pct = round(len(small) * 100 / len(chunk.chunks), 2)
good_pct = round(len(good) * 100 / len(chunk.chunks), 2)

print(f"safe chunks (under 2000):  --> {safe_count} ({safe_pct}%)")
print(f"small chunks (under 250):   --> {len(small)} ({small_pct}%)")
print(f"big chunks (over 2000):    --> {len(ext)}")
print(f"good chunks (over 800, below 2000):    --> {len(good)} ({good_pct}%)")
print(f"total number of chunks:    --> {len(chunk.chunks)}")

total = sum(ch.last_character_index - ch.first_character_index
            for ch in chunk.chunks)

print()
print()
print("Average length of chunks:  -->", round(total / len(chunk.chunks), 2))
