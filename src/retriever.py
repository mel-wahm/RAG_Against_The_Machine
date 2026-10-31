import json
from src.models import StudentSearchResults, MinimalSearchResults
from src.indexer import Indexer
from tqdm import tqdm
from pathlib import Path


class Retriever():
    def __init__(self, index: Indexer) -> None:
        self.index = index

    def answer_dataset(self, questions_file: str,
                       save_directory: str, k: int) -> None:
        with open(questions_file) as f:
            questions: dict[str, list[dict[str, str]]] = json.load(f)
        rag_questions: list[dict[str, str]] = questions["rag_questions"]
        answers = []
        for q in tqdm(rag_questions, desc="Answering the questions"):
            chunks = []
            top_scores = self.index.bm25(q["question"], k)
            for score in top_scores:
                chunks.append(self.index.chunks[score[0]])
            answer = MinimalSearchResults(question_id=q["question_id"],
                                          question=q["question"],
                                          retrieved_sources=chunks)
            answers.append(answer)
        student_answers = StudentSearchResults(search_results=answers,
                                               k=k)
        Path(save_directory).parent.mkdir(parents=True, exist_ok=True)
        with open(save_directory, "w") as f:
            f.write(student_answers.model_dump_json(indent=4))
