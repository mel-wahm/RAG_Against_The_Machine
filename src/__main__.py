from src.chunker import Chunker
# from src.models import MinimalSource
chunk = Chunker()
ext = [ch for ch in chunk.chunks if ch.last_character_index - ch.first_character_index
        > 2000]
small = [ch for ch in chunk.chunks if ch.last_character_index - ch.first_character_index
        < 100]
# for ch in chunk.chunks:
#     print(ch, ch.last_character_index - ch.first_character_index)

print("safe chunks (under 2000):  -->", len(chunk.chunks) - len(ext))
print("small chunks (under 50):   -->", len(small), f"({round(len(small) * 100 / len(chunk.chunks), 2)}%)")
print("big chunks (over 2000):    -->", len(ext))
print("total number of chunks:    -->", len(chunk.chunks))

"""

for node in content:
            s, e = self.chunk(node, lines_offsets)
            if s_buff is None:
                s_buff = s
                e_buff = e
                continue
            if e - s > self.max_chunk_size:
                if s_buff is not None:
                    start.append(s_buff)
                    end.append(e_buff)
                    s_buff, e_buff = None, None
                start.append(s)
                end.append(e)
            elif e - s_buff > self.max_chunk_size:
                start.append(s_buff)
                end.append(e_buff)
                s_buff = s
                e_buff = e
            else:
                e_buff = e
        if s_buff is not None:
            start.append(s_buff)
            end.append(e_buff)


safe chunks (under 2000):  --> 4930
small chunks (under 50):   --> 65 (0.91%)
big chunks (over 2000):    --> 2237
total number of chunks:    --> 7167
"""
