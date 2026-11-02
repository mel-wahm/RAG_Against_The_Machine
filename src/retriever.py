import json
from src.models import StudentSearchResults, MinimalSearchResults, RagDataset, AnsweredQuestion
from src.indexer import Indexer
from tqdm import tqdm
from pathlib import Path


class Retriever:
    def __init__(self, index: Indexer) -> None:
        self.index = index

    def search_dataset(self, questions_file: str,
                       save_directory: str, k: int) -> None:
        with open(questions_file) as f:
            questions: dict[str, list[dict[str, str]]] = json.load(f)
        rag_questions: list[dict[str, str]] = questions["rag_questions"]
        qu = []
        answers = []
        for q in tqdm(rag_questions, desc="Answering the questions"):
            chunks = []
            top_scores = self.index.bm25(q["question"], k)
            for score in top_scores:
                chunks.append(self.index.chunks[score[0]])
            qu.append(AnsweredQuestion(
                question_id=q["question_id"],
                question=q["question"],
                sources=chunks,
                answer="")

            )
            answer = MinimalSearchResults(question_id=q["question_id"],
                                          question=q["question"],
                                          retrieved_sources=chunks)
            answers.append(answer)
        student_answers = StudentSearchResults(search_results=answers,
                                               k=k)
        output_file = Path(questions_file).name
        Path(save_directory).mkdir(parents=True, exist_ok=True)
        with open(Path(save_directory) / Path(output_file), "w") as f:
            f.write(student_answers.model_dump_json(indent=4))
        dump = RagDataset(rag_questions=qu)
        with open("Rag_dataset.json", "w") as f:
            f.write(dump.model_dump_json(indent=4))
