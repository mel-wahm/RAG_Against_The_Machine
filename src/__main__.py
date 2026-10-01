from src.chunker import Chunker
from src.models import MinimalSource
chunk = Chunker()
# ext = [ch for ch in chunk.chunks if (ch.last_character_index - ch.first_character_index) > 2000]

# print(len(chunk.chunks))
# print(len(ext)) # 1261
# for e in ext:
    # print(e)
#file_path='data/raw/vllm-0.10.1/vllm/envs.py' first_character_index=8753 last_character_index=49085