import json
from src.models import StudentSearchResults, MinimalSearchResults, MinimalSource
from indexer import Indexer
from chunker import Chunker


indexer = Indexer(Chunker(2000, "data/raw").chunks)

def read_questions(file_path: str):
    with open(file_path) as f:
        questions = json.load(f)
    return questions

question: dict[str, str] = read_questions("data/datasets/UnansweredQuestions/dataset_code_public.json")["rag_questions"]

answers = []

for n, q in enumerate(question):
    # print(n, flush=True)
    scores = indexer.bm25(q["question"], 5)
    chunks = []
    for score, _ in scores:
        chunks.append(indexer.chunks[score])
    answer = MinimalSearchResults(question_id=q["question_id"],
                        question=q["question"],
                        retrieved_sources=chunks)
    answers.append(answer)

result = StudentSearchResults(search_results=answers, k=5)
with open("answers.json", "w") as f:
    f.write(result.model_dump_json(indent=4))
