import json
from pathlib import Path
from pydantic import ValidationError
from tqdm import tqdm
from src.models import (
    RagDataset,
    StudentSearchResults,
    MinimalSearchResults,
    MinimalSource,
)
from src.indexer import Indexer
from src.embedding import Embedder


class Retriever:
    def __init__(self, index: Indexer) -> None:
        self.index = index
        self.emb = Embedder(index)  

    def rrf(self, lex: list[int],
            emb: list[int], k: int) -> list[int]:
        dic = {a: 0.0 for a in lex + emb}
        for s in dic:
            for score in (lex, emb):
                if s in score:
                    mult = 1 if score == emb else 1.02
                    dic[s] += (1 / (60 + score.index(s))) * mult
        return (sorted(dic, key=lambda x: dic[x], reverse=True)[:k])

    def search_query(self, query: str, k: int) -> list[MinimalSource]:
        lex_top_scores = self.index.bm25(query, k)
        emb_scores = self.emb.search(query, k)
        top_scores = self.rrf(lex_top_scores, emb_scores, k)
        return [self.index.chunks[chunk] for chunk in top_scores]

    def search_dataset(
        self, questions_file: str, save_directory: str, k: int
    ) -> None:
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

        try:
            dataset = RagDataset.model_validate(questions)
        except ValidationError:
            print(
                f"Error: File '{questions_file}' does not match "
                "expected schema (missing or invalid 'rag_questions')."
            )
            return

        answers = []
        for q in tqdm(
            dataset.rag_questions,
            desc="Answering the questions",
            colour="#21ac77",
            ascii="  ▓▒░░",
        ):
            chunks = self.search_query(q.question, k)
            answer = MinimalSearchResults(
                question_id=q.question_id,
                question=q.question,
                retrieved_sources=chunks,
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
