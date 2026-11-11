# RAG Project Status & Roadmap

## 1. Summary of Changes & Fixes

All recent fixes have been applied and documented with comments directly in the codebase:

### Robustness & Crash Prevention
* **[`src/rag.py`](src/rag.py)**:
  * Wrapped `Chunker`, `Indexer`, and `Embedder` in `RAG.index` inside a `try...except` block. This prevents unhandled tracebacks when `index` is called on empty or non-code directories.
  * Wrapped `RAG.evaluate` inside a `try...except` block to prevent unhandled tracebacks during evaluation.
* **[`src/evaluator.py`](src/evaluator.py)**:
  * Replaced `raise ValueError` when a question ID in student results is missing from the ground truth dataset with a clean, user-facing error message and graceful exit.
  * Replaced `raise KeyError` in `calculate_recall` with `continue` to safely skip missing IDs rather than crashing.
* **[`src/chunker.py`](src/chunker.py)**:
  * Replaced `assert hasattr(class_node, "body")` with a safe conditional check to prevent `AssertionError` in production.
  * Broadened `python_chunker` exception handling from `(SyntaxError, UnicodeDecodeError)` to `except Exception:` to protect against permission restrictions, missing symlinks, or OS I/O errors.
* **[`src/generator.py`](src/generator.py)**:
  * Wrapped `Path(chunk.file_path).read_text()` inside `prepare_prompt` in a `try...except Exception:` block so that any moved, renamed, or deleted file after indexing does not crash generation.
* **[`src/indexer.py`](src/indexer.py)**:
  * Guarded `self.chunks_average_length` calculation against `ZeroDivisionError` when the chunk list is empty.
  * Guarded the penalty ratio calculation against division by zero if average chunk length is zero.
  * Fixed typo in warning message (`"meaninful"` → `"meaningful"`).
* **[`src/__main__.py`](src/__main__.py)**:
  * Added `sys.exit(1)` inside the top-level exception handlers so unexpected errors properly return a non-zero exit status to shell test harnesses.

### Verification & Quality
* `uv run make lint`: Passed with **0 errors** across all 11 source files (`flake8` + `mypy`).
* All degenerate edge cases (empty directory indexing, mismatched question IDs, non-positive `k`, invalid `k`) exit cleanly without unhandled tracebacks.

---

## 2. What Is Left to Finish the RAG Project

To complete the project for final 42 evaluation and peer defense, the following tasks remain:

### A. Mandatory `README.md` (Highest Priority)
The repository currently has an empty `README.md`. Chapter VIII of the subject requires a comprehensive `README.md` containing:
1. **Header**: Exactly `*This project has been created as part of the 42 curriculum by <your_login>.*` as the first line in italics.
2. **Project Description & Setup**: Explanation of the project and exact installation instructions (`uv sync`).
3. **Usage Guide**: Examples for every CLI command (`index`, `search`, `search_dataset`, `answer`, `answer_dataset`, `evaluate`).
4. **AI Usage Statement**: Mandatory statement detailing the AI tools used, prompts, and reasoning (as specified in Chapter III).
5. **System Architecture**:
   - Chunking Strategy (AST-based parsing for Python classes/functions, header-aware Markdown chunking, sliding text windows).
   - Inverted Index & BM25 Scoring (custom tokenizer, stopword filtering, length normalization).
   - Dense Embeddings (`all-MiniLM-L6-v2`) and Reciprocal Rank Fusion (RRF) formula.
   - Generation pipeline using `Qwen/Qwen3-0.6B` with Left-Padding and CPU thread optimization.
6. **Benchmark & Evaluation Results**:
   - Docs Recall@5: ~89.0% (Passing threshold $\ge 80\%$)
   - Code Recall@5: ~79.8% (Passing threshold $\ge 50\%$)
   - Average query search latency (~100 ms) and dataset batch throughput.
7. **Design Decisions & Trade-offs**: Discussion on memory management, atomic persistence, and multi-threading.

### B. Final Peer Defense Dry Run
* Test all CLI commands in a fresh terminal shell:
  * `uv run python -m src search "What is LoRA?" --k 3`
  * `uv run python -m src answer "What is LoRA?" --k 1`
  * `uv run python -m src search_dataset data/datasets/AnsweredQuestions/dataset_docs_public.json 5 output/`
  * `uv run python -m src answer_dataset output/dataset_docs_public.json output/`
  * `uv run python -m src evaluate output/dataset_docs_public.json data/datasets/AnsweredQuestions/dataset_docs_public.json`
* Run the official Moulinette binary on the outputs:
  `/home/mel-wahm/projects/moulinette-ubuntu evaluate_student_search_results output/dataset_docs_public.json data/datasets/AnsweredQuestions/dataset_docs_public.json`
* Confirm git working tree is clean and `git status` shows no untracked artifacts.
