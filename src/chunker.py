import ast
from pathlib import Path
from src.models import MinimalSource


class Buffer:
    """
    class for saving multiple small chunks
    and merge them into one chunk"""

    def __init__(
        self, chunks: list[tuple[int, int]], max_chunk_size: int
    ) -> None:
        self.max_chunk_size = max_chunk_size
        self.start: int | None = None
        self.end: int | None = None
        self.chunks = chunks

    def add(self, chunk: tuple[int, int]) -> None:
        """attempts to add a chunks, if we will exceed max chunk
        size, we commit the buffer and create a new one"""
        start, end = chunk
        if self.start is None:
            self.start, self.end = start, end
        elif end - self.start <= self.max_chunk_size:
            self.end = end
        else:
            self.flush()
            self.start, self.end = start, end

    def flush(self) -> None:
        if self.start is not None and self.end is not None:
            self.chunks.append((self.start, self.end))
        self.start, self.end = None, None


class Chunker:
    """
    takes in a path to folder, and chunks the supported files into
    meaninful chunks to better optimize the answers we get with AI
    """

    def __init__(self, max_size: int, data_path: str) -> None:
        self.max_size = max_size
        self.data_path = data_path
        self.python_files, self.markdown_files, self.text_files = (
            self.load_files()
        )
        self.chunks = self.create_chunks()

    def load_files(self) -> list[list[str]]:
        python_files = []
        markdown_files = []
        text_files = []
        path = Path(self.data_path)
        for file in path.rglob("*"):
            if str(file).endswith(".py"):
                python_files.append(str(file))
            if str(file).endswith(".md"):
                markdown_files.append(str(file))
            if str(file).endswith(".txt"):
                text_files.append(str(file))
        return [python_files, markdown_files, text_files]

    def create_chunks(self) -> list[MinimalSource]:
        chunks: list[MinimalSource] = []
        for file in self.python_files:
            chunks.extend(self.python_chunker(file))
        for file in self.markdown_files:
            chunks.extend(self.markdown_chunker(file))
        for file in self.text_files:
            chunks.extend(self.text_chunker(file))
        return chunks

    def get_offsets(
        self, node: ast.stmt, files_offsets: list[int]
    ) -> tuple[int, int]:
        """
        takes an AST node, and returns the character
        offsets where it starts and where it ends
        """

        if node.end_col_offset is None or node.end_lineno is None:
            return (0, 0)

        if hasattr(node, "decorator_list") and node.decorator_list:
            start_line = node.decorator_list[0].lineno
            start_line_offs = node.decorator_list[0].col_offset
        else:
            start_line = node.lineno
            start_line_offs = node.col_offset
        start_off = files_offsets[start_line - 1] + start_line_offs
        end_off = files_offsets[node.end_lineno - 1] + node.end_col_offset
        return (start_off, end_off)

    def chunk_oversized_class(
        self,
        class_node: ast.stmt,
        spans: list[tuple[int, int]],
        files_offsets: list[int],
        source: str,
    ) -> None:

        chunk_start: int | None = \
            self.get_offsets(class_node, files_offsets)[0]
        member_buffer = Buffer(spans, self.max_size)
        assert (hasattr(class_node, "body"))
        for node in class_node.body:
            start = (
                self.get_offsets(node, files_offsets)[0]
                if chunk_start is None
                else chunk_start
            )
            chunk_start = None
            end = self.get_offsets(node, files_offsets)[1]
            if end - start > self.max_size:
                if member_buffer.start is not None:
                    member_buffer.flush()
                self.chunk_by_lines(start, end, spans, source)

            else:
                member_buffer.add((start, end))
        if member_buffer.start is not None:
            member_buffer.flush()

    def split_long_line(self, spans: list[tuple[int, int]],
                        start: int, end: int) -> None:
        curr = start

        while curr + self.max_size < end:
            spans.append((curr, curr + self.max_size))
            curr += self.max_size

        spans.append((curr, end))

    def chunk_by_lines(
        self,
        start: int,
        end: int,
        spans: list[tuple[int, int]],
        source: str,
        overlap: int = 150,
    ) -> None:
        """
        Splits an oversized node into line-based chunks under max_size.
        """
        # this marks the beginning and ending offsets of the node
        lines = source[start:end].splitlines(keepends=True)
        lines_offsets = [0]
        for line in lines:
            lines_offsets.append(lines_offsets[-1] + len(line))
        start_line = 0
        lines_len = len(lines)
        while start_line < lines_len:
            end_line = start_line
            chunk_length = 0
            while (
                end_line < lines_len
                and chunk_length + len(lines[end_line]) <= self.max_size
            ):
                chunk_length += len(lines[end_line])
                end_line += 1
            if end_line == start_line:
                end_line += 1
                self.split_long_line(spans, start + lines_offsets[start_line],
                                     start + lines_offsets[end_line])
                start_line += 1
                continue
            chunk_s = start + lines_offsets[start_line]
            chunk_e = start + lines_offsets[end_line]
            spans.append((chunk_s, chunk_e))
            if end_line == lines_len:
                break
            overlap_line = end_line
            overlap_length = 0
            while overlap_line > start_line + 1:
                prev_endgth = len(lines[overlap_line - 1])
                if prev_endgth + overlap_length <= overlap:
                    overlap_line -= 1
                    overlap_length += prev_endgth
                else:
                    break
            start_line = overlap_line

    def python_chunker(self, file_name: str) -> list[MinimalSource]:
        """
        takes in a python file and returns
        a list of chunks and their offsets
        """
        spans: list[tuple[int, int]] = []
        class_buffer = Buffer(spans, self.max_size)
        function_buffer = Buffer(spans, self.max_size)
        modules_buffer = Buffer(spans, self.max_size)
        with open(file_name) as f:
            source = f.read()
        try:
            content = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            return []

        def flush_all_expect(active_buffer: Buffer | None = None) -> None:
            for buffer in (modules_buffer, function_buffer, class_buffer):
                if buffer is not active_buffer:
                    buffer.flush()

        # a list representing each line and which file-character it starts in
        files_offsets = [0]
        for line in source.splitlines(keepends=True):
            files_offsets.append(files_offsets[-1] + len(line))

        for node in content.body:
            start, end = self.get_offsets(node, files_offsets)
            if isinstance(node, ast.ClassDef):
                flush_all_expect(class_buffer)
                if end - start > self.max_size:
                    class_buffer.flush()
                    self.chunk_oversized_class(
                        node, spans, files_offsets, source
                    )
                else:
                    class_buffer.add((start, end))
            elif type(node) in [ast.FunctionDef, ast.AsyncFunctionDef]:
                flush_all_expect(function_buffer)
                if end - start > self.max_size:
                    function_buffer.flush()
                    self.chunk_by_lines(start, end, spans, source)
                else:
                    function_buffer.add((start, end))
            else:
                flush_all_expect(modules_buffer)
                if end - start > self.max_size:
                    modules_buffer.flush()
                    self.chunk_by_lines(start, end, spans, source)
                else:
                    modules_buffer.add((start, end))
        flush_all_expect()
        return [
            MinimalSource(
                file_path=file_name,
                first_character_index=s,
                last_character_index=e,
            )
            for s, e in spans
        ]

    def markdown_chunker(self, file_path: str) -> list[MinimalSource]:
        try:
            with open(file_path) as f:
                source = f.read()
        except Exception:
            return []
        if not source.strip():
            return []
        in_code_block = False
        lines = list(source.splitlines(keepends=True))
        spans: list[tuple[int, int]] = []
        markdown_buffer: Buffer = Buffer(spans, self.max_size)

        def is_header(line: str) -> bool:
            space_stripped = line.lstrip()
            if len(line) - len(space_stripped) >= 4:
                return False
            stripped_line = space_stripped.lstrip("#")
            if not stripped_line:
                return False
            return (
                stripped_line[0] in (" ", "\t")
                and 1 <= len(space_stripped) - len(stripped_line) <= 6
            )
        line_offsets = [0]
        for line in lines:
            line_offsets.append(line_offsets[-1] + len(line))

        for num, line in enumerate(lines):
            if line.lstrip().startswith("```") or \
             line.lstrip().startswith("~~~"):
                in_code_block = not in_code_block
            line_is_header = is_header(line) and not in_code_block
            if line_is_header:
                markdown_buffer.flush()
            if len(line) > self.max_size:
                markdown_buffer.flush()
                self.split_long_line(spans, line_offsets[num],
                                     line_offsets[num + 1])
            else:
                markdown_buffer.add((line_offsets[num], line_offsets[num + 1]))
        markdown_buffer.flush()
        return [MinimalSource(file_path=file_path,
                first_character_index=s,
                last_character_index=e) for s, e in spans]

    def text_chunker(self, file_path: str) -> list[MinimalSource]:
        try:
            with open(file_path) as f:
                source = f.read()
        except Exception:
            return []
        spans : list[tuple[int, int]]= []
        self.chunk_by_lines(0, len(source), spans, source)
        return [MinimalSource(file_path=file_path,
                              first_character_index=s,
                              last_character_index=e) for s, e in spans]
