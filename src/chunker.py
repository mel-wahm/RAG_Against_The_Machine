from pathlib import Path
from src.models import MinimalSource
import ast
from typing import Tuple


class Chunker():
    def __init__(self, max_chunk_size: int, data_path: str) -> None:
        self.max_chunk_size = max_chunk_size
        self.data_path = data_path
        self.python_files, \
            self.markdown_files, \
            self.text_files = self.load_files()
        self.big_chunks = (ast.FunctionDef, ast.ClassDef,
                           ast.AsyncFunctionDef)
        self.chunks = self.set_chunks()

    def load_files(self) -> Tuple[list[str], list[str], list[str]]:
        path = Path(self.data_path)
        files = list(str(f) for f in path.rglob("*") if f.is_file())
        python_files = [f for f in files if f.endswith(".py")]
        markdown_files = [f for f in files if f.endswith(".md")]
        text_files = [f for f in files if f.endswith(".txt")]
        return python_files, markdown_files, text_files

    def set_chunks(self) -> list[MinimalSource]:
        chunks = []
        for file in self.python_files:
            chunk = self.python_chunker(file)
            chunks.extend(chunk)
        return chunks

    def chunk(self, node: ast.stmt,
              lines_offsets: list[int]) -> Tuple[int, int]:
        if node.end_col_offset is None or node.end_lineno is None:
            return 0, 0
        if hasattr(node, "decorator_list") and node.decorator_list:
            line_no = node.decorator_list[0].lineno
        else:
            line_no = node.lineno
        s = lines_offsets[line_no - 1] + node.col_offset
        e = lines_offsets[node.end_lineno - 1] + node.end_col_offset
        return s, e

    def chunk_by_lines(self, s: int, e: int, source: str,
                       overlap: int = 150) -> list[Tuple[int, int]]:
        if e - s <= self.max_chunk_size:
            return [(s, e)]
        chunks: list[Tuple[int, int]] = []
        text = source[s:e]
        lines = text.splitlines(keepends=True)
        line_offsets = [0]
        for line in lines:
            line_offsets.append(line_offsets[-1] + len(line))

        line_start = 0   
        while line_start < len(lines):
            line_end = line_start
            line_length = 0
            while (line_end < len(lines)
                   and line_length + len(lines[line_end])
                   <= self.max_chunk_size):
                line_length += len(lines[line_end])
                line_end += 1

            if line_end == line_start:
                line_end += 1

            chunk_s = s + line_offsets[line_start]
            chunk_e = s + line_offsets[line_end]
            chunks.append((chunk_s, chunk_e))

            if line_end >= len(lines):
                break

            overlap_len = 0
            next_start_idx = line_end
            while next_start_idx > line_start + 1:
                cand_len = overlap_len + len(lines[next_start_idx - 1])
                if cand_len <= overlap:
                    overlap_len = cand_len
                    next_start_idx -= 1
                else:
                    break
            line_start = next_start_idx

        return chunks

    def python_chunker(self, file_path: str) -> list[MinimalSource]:
        with open(file_path) as f:
            source = f.read()
        content = ast.parse(source).body
        lines_offsets: list[int] = [0]
        for line in source.splitlines(keepends=True):
            lines_offsets.append(len(line) + lines_offsets[-1])
        start = []
        end = []
        s_buff, e_buff = None, None
        fn_s_buff, fn_e_buff = None, None
        for node in content:
            s, e = self.chunk(node, lines_offsets)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if s_buff is not None:
                    start.append(s_buff)
                    end.append(e_buff)
                    s_buff, e_buff = None, None
                if e - s > self.max_chunk_size:
                    if fn_s_buff is not None:
                        start.append(fn_s_buff)
                        end.append(fn_e_buff)
                        fn_s_buff, fn_e_buff = None, None
                    for cs, ce in self.chunk_by_lines(s, e, source):
                        start.append(cs)
                        end.append(ce)
                elif fn_s_buff is None:
                    fn_s_buff = s
                    fn_e_buff = e
                elif e - fn_s_buff > self.max_chunk_size:
                    start.append(fn_s_buff)
                    end.append(fn_e_buff)
                    fn_s_buff = s
                    fn_e_buff = e
                else:
                    fn_e_buff = e
            elif isinstance(node, ast.ClassDef):
                if s_buff is not None:
                    start.append(s_buff)
                    end.append(e_buff)
                    s_buff, e_buff = None, None
                if fn_s_buff is not None:
                    start.append(fn_s_buff)
                    end.append(fn_e_buff)
                    fn_s_buff, fn_e_buff = None, None
                if e - s > self.max_chunk_size:
                    sbuff, ebuff = None, None
                    for child in node.body:
                        s_, e_ = self.chunk(child, lines_offsets)
                        if e_ - s_ > self.max_chunk_size:
                            if sbuff is not None:
                                start.append(sbuff)
                                end.append(ebuff)
                                sbuff, ebuff = None, None
                            elif s is not None:
                                start.append(s)
                                end.append(s_)
                                s = None
                            for cs, ce in self.chunk_by_lines(
                                s_, e_, source
                            ):
                                start.append(cs)
                                end.append(ce)
                        elif sbuff is None:
                            if s is not None and e_ - s <= self.max_chunk_size:
                                sbuff = s
                            else:
                                if s is not None:
                                    start.append(s)
                                    end.append(s_)
                                sbuff = s_
                            s = None
                            ebuff = e_
                        elif e_ - sbuff > self.max_chunk_size:
                            start.append(sbuff)
                            end.append(ebuff)
                            sbuff = s_
                            ebuff = e_
                        else:
                            ebuff = e_
                    if sbuff is not None:
                        start.append(sbuff)
                        end.append(ebuff)
                else:
                    start.append(s)
                    end.append(e)
            elif e - s > self.max_chunk_size:
                if s_buff is not None:
                    start.append(s_buff)
                    end.append(e_buff)
                    s_buff, e_buff = None, None
                if fn_s_buff is not None:
                    start.append(fn_s_buff)
                    end.append(fn_e_buff)
                    fn_s_buff, fn_e_buff = None, None
                for cs, ce in self.chunk_by_lines(s, e, source):
                    start.append(cs)
                    end.append(ce)
            else:
                if fn_s_buff is not None:
                    start.append(fn_s_buff)
                    end.append(fn_e_buff)
                    fn_s_buff, fn_e_buff = None, None
                if s_buff is None:
                    s_buff = s
                    e_buff = e
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
        if fn_s_buff is not None:
            start.append(fn_s_buff)
            end.append(fn_e_buff)


        chunks: list[MinimalSource] = []
        for i in range(len(start)):
            chunks.append(MinimalSource(
                file_path=file_path,
                first_character_index=start[i],
                last_character_index=end[i]))
        return chunks
