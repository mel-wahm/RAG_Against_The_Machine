from pathlib import Path
from src.models import MinimalSource
import ast


class Chunker():
    def __init__(self) -> None:
        self.data_path = "test"
        self.python_files, \
            self.markdown_files, \
            self.text_files = self.load_files()
        print(self.python_chunker("src/__main__.py"))
        # self.chunks = self.set_chunks()

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
            print(node)
            if node.end_col_offset is None or node.end_lineno is None:
                continue
            if hasattr(node, "decorator_list") and node.decorator_list:
                line_no = node.decorator_list[0].lineno
            else:
                line_no = node.lineno
            start.append(lines_offsets[line_no - 1] + node.col_offset)
            end.append(lines_offsets[node.end_lineno - 1] +
                       node.end_col_offset)
        chunks: list[MinimalSource] = []
        for i in range(len(start)):
            chunks.append(MinimalSource(
                file_path=file_path,
                first_character_index=start[i],
                last_character_index=end[i]))
        return chunks
