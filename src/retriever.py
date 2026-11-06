import json
from pathlib import Path
from tqdm import tqdm
from src.models import StudentSearchResults, MinimalSearchResults
from src.indexer import Indexer
# from src.embedding import Embedder


class Retriever:
    def __init__(self, index: Indexer) -> None:
        self.index = index

    def search_dataset(
        self, questions_file: str, save_directory: str, k: int
    ) -> None:
        # self.emb = Embedder()
        path = Path(questions_file)
        if not path.is_file():
            print(f"Error: Questions file '{questions_file}' not found.")
            return

        try:
            with open(path) as f:
                questions = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: File '{questions_file}' contains invalid JSON.")
            return
        except Exception as e:
            print(f"Error reading '{questions_file}': {e}")
            return

        if not isinstance(questions, dict) or "rag_questions" not in questions:
            print(
                f"Error: File '{questions_file}' is missing 'rag_questions'."
            )
            return

        rag_questions = questions["rag_questions"]
        answers = []
        for q in tqdm(
            rag_questions,
            desc="Answering the questions",
            colour="#21ac77",
            ascii="  ▓▒░░",
        ):
            chunks = []
            q_text = q.get("question", "") if isinstance(q, dict) else ""
            q_id = q.get("question_id", "") if isinstance(q, dict) else ""

            lex_top_scores = self.index.bm25(q_text, k)
            for score in lex_top_scores:
                chunks.append(self.index.chunks[score[0]])
            answer = MinimalSearchResults(
                question_id=q_id, question=q_text, retrieved_sources=chunks
            )
            answers.append(answer)
        student_answers = StudentSearchResults(search_results=answers, k=k)
        output_file = path.name
        save_dir = Path(save_directory)
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
            with open(save_dir / output_file, "w") as f:
                f.write(student_answers.model_dump_json(indent=4))
        except Exception as e:
            print(f"Error saving results to '{save_directory}': {e}")
