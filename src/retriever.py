import json
from src.models import StudentSearchResults, MinimalSearchResults
from src.indexer import Indexer
from src.chunker import Chunker


class Retriever():
    def __init__(self,
                 chunks: Chunker,
                 output_file: str = "answers.json",
                 questions_file: str =
                 "data/datasets/UnansweredQuestions/dataset_code_public.json",
                 k: int = 5):
        self.indexer = Indexer(chunks)
        self.k = k
        self.output_file = output_file
        self.questions_file = questions_file
        self.questions = self.read_questions()
        self.answers = self.answer_questions()
        self.output_answers()

    def read_questions(self) -> list[dict[str, str]]:
        with open(self.questions_file) as f:
            questions: dict[str, list[dict[str, str]]] = json.load(f)
        return questions["rag_questions"]

    def answer_questions(self) -> list[MinimalSearchResults]:
        answers = []
        for q in self.questions:
            chunks = []
            top_scores = self.indexer.bm25(q["question"], self.k)
            for score in top_scores:
                chunks.append(self.indexer.chunks[score[0]])
            answer = MinimalSearchResults(question_id=q["question_id"],
                                          question=q["question"],
                                          retrieved_sources=chunks)
            answers.append(answer)
        return answers

    def output_answers(self) -> None:
        student_answers = StudentSearchResults(search_results=self.answers,
                                               k=self.k)
        with open(self.output_file, "w") as f:
            f.write(student_answers.model_dump_json(indent=4))
