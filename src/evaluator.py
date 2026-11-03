from src.models import RagDataset, StudentSearchResults, \
    MinimalSource, AnsweredQuestion, MinimalSearchResults, UnansweredQuestion
import json


class Evaluator:
    def __init__(self, student_search_results_path: str,
                 dataset_path: str):
        self.student_search_results_path = student_search_results_path
        self.dataset_path = dataset_path

    def calculate_iou(self, first_chunk: MinimalSource,
                      second_chunk: MinimalSource) -> float:
        if first_chunk.file_path != second_chunk.file_path:
            return 0.0
        f_start, f_end = first_chunk.first_character_index, \
            first_chunk.last_character_index
        s_start, s_end = second_chunk.first_character_index, \
            second_chunk.last_character_index
        inter = max(0, min(f_end, s_end) - max(f_start, s_start))
        union = (f_end - f_start) + (s_end - s_start) - inter
        if not union:
            return 0.0
        return inter / union

    def calculate_recall(self, r: int,
                         student_answers: list[MinimalSearchResults],
                         ids: dict[str, AnsweredQuestion | UnansweredQuestion],
                         ) -> float:
        recall = 0.0
        for answer in student_answers:
            if answer.question_id not in ids:
                raise ValueError(f"{answer.question_id} not in data answers")
            truth = ids[answer.question_id]
            assert hasattr(truth, "sources")
            truth = truth.sources
            for t in truth:
                current = 0
                for a in answer.retrieved_sources[:r]:
                    rec = self.calculate_iou(a, t)
                    if rec >= 0.05:
                        current += 1
                        break
                recall += current / len(truth)
        return recall

    def evaluate(self) -> None:
        with open(self.dataset_path) as f:
            dataset = json.load(f)
        with open(self.student_search_results_path) as f:
            search_result = json.load(f)
        user_answers = StudentSearchResults.model_validate(search_result)\
            .search_results
        dataset_answers = RagDataset.model_validate(dataset).rag_questions
        ids = {data.question_id: data for data in dataset_answers}
        total = len(dataset_answers)
        recall = {
            1: 0.0,
            3: 0.0,
            5: 0.0,
            10: 0.0,
        }

        if not all(hasattr(truth, "sources") for truth in ids.values()):
            print("Evaluation Error: You can't check your "
                  "answers against Unansweredquestions, "
                  "please use Answeredquestions dataset")
            return

        for r in recall:
            recall[r] = self.calculate_recall(r,
                                              user_answers,
                                              ids
                                              )

        print()
        print("🎯 Evaluation Results")
        print("========================================")
        print()
        print(f"📊 Questions evaluated: {total}")
        for r in recall:
            print(f"📈 Recall@{r}: {(recall[r] / total):.3f}",
                  f"    ({(recall[r] * 100 / total):.1f}%)")
        print()
        print({f"recall{r}": recall[r] / total for r in sorted(recall)})
