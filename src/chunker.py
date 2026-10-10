from pathlib import Path
import ast
from typing import Tuple, List, Optional
from src.models import MinimalSource


class SpanBuffer:
    """
    Greedily aggregates contiguous start and end character offsets into chunks.
    Flushes to the output list when adding an offset would exceed max_chunk_size.
    """
    def __init__(self, max_chunk_size: int, output_spans: List[Tuple[int, int]]) -> None:
        self.max_chunk_size = max_chunk_size
        self.output_spans = output_spans
        self.start: Optional[int] = None
        self.end: Optional[int] = None

    def add(self, start: int, end: int) -> None:
        """Add a span. Flushes if the resulting size would exceed max_chunk_size."""
        if self.start is None:
            self.start, self.end = start, end
        elif end - self.start <= self.max_chunk_size:
            self.end = end
        else:
            self.flush()
            self.start, self.end = start, end

    def flush(self) -> None:
        """Commit the current buffer to output_spans and reset."""
        if self.start is not None and self.end is not None:
            self.output_spans.append((self.start, self.end))
            self.start, self.end = None, None


class Chunker:
    """
    AST-based document chunker that splits Python code into semantically coherent,
    size-bounded chunks for retrieval-augmented generation (RAG).
    """
    def __init__(self, max_chunk_size: int, data_path: str) -> None:
        self.max_chunk_size = max_chunk_size
        self.data_path = data_path
        self.python_files, self.markdown_files, self.text_files = self.load_files()
        self.chunks = self.set_chunks()

    def load_files(self) -> Tuple[List[str], List[str], List[str]]:
        """Recursively scan data_path (with ~ expansion) and group files by extension, ignoring hidden directories."""
        path = Path(self.data_path).expanduser().resolve()
        files = [
            str(f) for f in path.rglob("*")
            if f.is_file() and not any(part.startswith(".") for part in f.parts[:-1])
        ]
        python_files = [f for f in files if f.endswith(".py")]
        markdown_files = [f for f in files if f.endswith(".md")]
        text_files = [f for f in files if f.endswith(".txt")]
        return python_files, markdown_files, text_files

    def set_chunks(self) -> List[MinimalSource]:
        """Parse all discovered Python files and return their chunks."""
        chunks: List[MinimalSource] = []
        for file in self.python_files:
            try:
                chunks.extend(self.python_chunker(file))
            except (SyntaxError, UnicodeDecodeError):
                continue
        return chunks

    def get_node_span(self, node: ast.stmt, lines_offsets: List[int]) -> Tuple[int, int]:
        """Return the (start, end) character offsets of an AST node including decorators."""
        if node.end_col_offset is None or node.end_lineno is None:
            return 0, 0
        line_no = node.decorator_list[0].lineno if \
            hasattr(node, "decorator_list") and node.decorator_list else node.lineno
        start_offset = lines_offsets[line_no - 1] + node.col_offset
        end_offset = lines_offsets[node.end_lineno - 1] + node.end_col_offset
        return start_offset, end_offset

    def chunk_by_lines(self, start_offset: int, end_offset: int, source: str, overlap: int = 150) -> List[Tuple[int, int]]:
        """
        Split a span [start_offset:end_offset] along newline boundaries using a sliding window.
        Includes backward line overlap to preserve context between chunks.
        """
        if end_offset - start_offset <= self.max_chunk_size:
            return [(start_offset, end_offset)]

        chunks: List[Tuple[int, int]] = []
        lines = source[start_offset:end_offset].splitlines(keepends=True)
        line_offsets = [0]
        for line in lines:
            line_offsets.append(line_offsets[-1] + len(line))

        line_start = 0
        while line_start < len(lines):
            line_end = line_start
            line_length = 0
            while line_end < len(lines) and line_length + len(lines[line_end]) <= self.max_chunk_size:
                line_length += len(lines[line_end])
                line_end += 1

            if line_end == line_start:
                line_end += 1

            chunks.append((start_offset + line_offsets[line_start], start_offset + line_offsets[line_end]))
            if line_end >= len(lines):
                break

            # Slide backwards from line_end to capture overlapping lines up to `overlap`
            overlap_len = 0
            next_start_idx = line_end
            while next_start_idx > line_start + 1:
                candidate_len = overlap_len + len(lines[next_start_idx - 1])
                if candidate_len <= overlap:
                    overlap_len = candidate_len
                    next_start_idx -= 1
                else:
                    break
            line_start = next_start_idx

        return chunks

    def _chunk_large_class(self, node: ast.ClassDef, class_start: int, lines_offsets: List[int],
                           source: str, spans: List[Tuple[int, int]]) -> None:
        """
        Split an oversized class (> max_chunk_size) member by member, ensuring the class
        declaration and initial comments are mixed into the first member chunk.
        """
        member_buffer = SpanBuffer(self.max_chunk_size, spans)
        pending_class_header: Optional[int] = class_start

        for child in node.body:
            child_start, child_end = self.get_node_span(child, lines_offsets)

            # Child function or block exceeds max_chunk_size on its own
            if child_end - child_start > self.max_chunk_size:
                chunk_start = pending_class_header if pending_class_header is not None else (member_buffer.start or child_start)
                pending_class_header = None
                member_buffer.start, member_buffer.end = None, None
                spans.extend(self.chunk_by_lines(chunk_start, child_end, source))

            # First member: attach class header if still pending
            elif member_buffer.start is None:
                chunk_start = pending_class_header if pending_class_header is not None else child_start
                pending_class_header = None
                if child_end - chunk_start <= self.max_chunk_size:
                    member_buffer.start, member_buffer.end = chunk_start, child_end
                else:
                    spans.extend(self.chunk_by_lines(chunk_start, child_end, source))

            # Buffer overflow: commit existing chunk and start anew
            elif child_end - member_buffer.start > self.max_chunk_size:
                member_buffer.flush()
                member_buffer.start, member_buffer.end = child_start, child_end
            else:
                member_buffer.end = child_end

        member_buffer.flush()

    def python_chunker(self, file_path: str) -> List[MinimalSource]:
        """
        Segment a Python file into semantically coherent chunks using AST analysis.
        Buffers top-level statements, small functions, and small classes into clean units.
        """
        with open(file_path) as f:
            source = f.read()
        content = ast.parse(source).body

        lines_offsets: List[int] = [0]
        for line in source.splitlines(keepends=True):
            lines_offsets.append(len(line) + lines_offsets[-1])

        spans: List[Tuple[int, int]] = []
        module_buffer = SpanBuffer(self.max_chunk_size, spans)
        func_buffer = SpanBuffer(self.max_chunk_size, spans)
        class_buffer = SpanBuffer(self.max_chunk_size, spans)

        def flush_all_except(active_buffer: Optional[SpanBuffer] = None) -> None:
            """Flush buffers when switching AST statement domains."""
            for buf in (module_buffer, func_buffer, class_buffer):
                if buf is not active_buffer:
                    buf.flush()

        for node in content:
            node_start, node_end = self.get_node_span(node, lines_offsets)

            # 1. Functions: buffer small functions; split oversized functions by lines
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                flush_all_except(func_buffer)
                if node_end - node_start > self.max_chunk_size:
                    func_buffer.flush()
                    spans.extend(self.chunk_by_lines(node_start, node_end, source))
                else:
                    func_buffer.add(node_start, node_end)

            # 2. Classes: buffer small classes; unpack oversized classes member-by-member
            elif isinstance(node, ast.ClassDef):
                flush_all_except(class_buffer)
                if node_end - node_start > self.max_chunk_size:
                    class_buffer.flush()
                    self._chunk_large_class(node, node_start, lines_offsets, source, spans)
                else:
                    class_buffer.add(node_start, node_end)

            # 3. Other oversized top-level statements (e.g. huge data dicts/lists)
            elif node_end - node_start > self.max_chunk_size:
                flush_all_except()
                spans.extend(self.chunk_by_lines(node_start, node_end, source))

            # 4. General module-level statements (imports, variables, expressions)
            else:
                flush_all_except(module_buffer)
                module_buffer.add(node_start, node_end)

        flush_all_except()
        return [MinimalSource(file_path=file_path, first_character_index=s, last_character_index=e) for s, e in spans]
