import json
from src.models import StudentSearchResults, MinimalSearchResults
from src.indexer import Indexer
from src.chunker import Chunker


class Retriever():
    def __init__(self,
                 document_type: str = "code",
                 output_file: str = "answers.json",
                 questions_file: str =
                 "data/datasets/UnansweredQuestions/dataset_code_public.json",
                 k: int = 5):
        self.document_type = document_type
        chunks = Chunker(2000, "data/raw").chunks
        if self.document_type == "code":
            self.indexer = Indexer([chunk for chunk in chunks if
                                    chunk.file_path.endswith(".py")],
                                   0.5, 0.8)
        else:
            self.indexer = Indexer([chunk for chunk in chunks if not
                                    chunk.file_path.endswith(".py")],
                                   1.4, 0.75)
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


document_type = "docs"
question_file = "data/datasets/UnansweredQuestions/dataset_docs_public.json"
RET = Retriever(document_type=document_type, questions_file=question_file)
