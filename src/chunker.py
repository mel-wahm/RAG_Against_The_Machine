from pathlib import Path
from src.models import MinimalSource
import ast
from typing import Tuple


class Chunker():
    def __init__(self) -> None:
        self.data_path = "data/raw/vllm-0.10.1/"
        self.python_files, \
            self.markdown_files, \
            self.text_files = self.load_files()
        self.chunks = self.set_chunks()

    def load_files(self) -> list[list[str]]:
        path = Path(self.data_path)
        files = list(str(f) for f in path.rglob("*") if f.is_file())
        python_files = [f for f in files if f.endswith(".py")]
        markdown_files = [f for f in files if f.endswith(".md")]
        text_files = [f for f in files if f.endswith(".txt")]
        return [python_files, markdown_files, text_files]

    def set_chunks(self) -> list[MinimalSource]:
        chunks = []
        for file in self.python_files:
            chunk = self.python_chunker(file)
            chunks.extend(chunk)
        return chunks

    def chunk(self, node: ast.stmt,
                        lines_offsets: list[int])\
                            -> list[Tuple[int, int]]:
        chunks = []
        if node.end_col_offset is None or node.end_lineno is None:
            return chunks
        if hasattr(node, "decorator_list") and node.decorator_list:
            line_no = node.decorator_list[0].lineno
        else:
            line_no = node.lineno
        s = lines_offsets[line_no - 1] + node.col_offset
        e = lines_offsets[node.end_lineno - 1] + node.end_col_offset
        if e - s > 2000 and hasattr(node, "body"):
            for child in node.body:
                result = self.chunk(child, lines_offsets)
                chunks.extend(result)
        else:
            if e - s > 2000:
                print(node)
            chunks.append((s, e))
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
        for node in content:
            index = self.chunk(node, lines_offsets)
            if not index:
                continue
            for chunk in index:
                s, e = chunk
                start.append(s)
                end.append(e)
        
        chunks: list[MinimalSource] = []
        for i in range(len(start)):
            chunks.append(MinimalSource(
                file_path=file_path,
                first_character_index=start[i],
                last_character_index=end[i]))
        return chunks
