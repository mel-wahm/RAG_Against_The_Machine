from src.chunker import Chunker
# from src.models import MinimalSource
chunk = Chunker()
ext = [ch for ch in chunk.chunks if
       (ch.last_character_index -
        ch.first_character_index) > 2000]
