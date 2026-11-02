from src.models import RagDataset, StudentSearchResults
import json


class Evaluator:
    def __init__(self, student_search_results_path: str,
                   dataset_path: str):
        self.student_search_results_path = student_search_results_path
        self.dataset_path = dataset_path



    def evaluate(self) -> None:
        with open(self.dataset_path) as f:
            dataset = json.load(f)
        with open(self.student_search_results_path) as f:
            search_result = json.load(f)
        user_answers = StudentSearchResults.model_validate(search_result).search_results
        dataset_answers = RagDataset.model_validate(dataset).rag_questions
        ids = {data.question_id: data for data in dataset_answers}
        # score = 0
        total = len(dataset_answers)
        recall = {
            1: 0.0,
            3: 0.0,
            5: 0.0,
            10: 0.0,
        }

        for answer in user_answers:
            if answer.question_id not in ids:
                raise ValueError("bruh")
            truth = ids[answer.question_id].sources[0]
            for rec, source in enumerate(answer.retrieved_sources):
                if source.file_path != truth.file_path:
                    continue
                my_start, my_end = source.first_character_index, source.last_character_index
                start, end = truth.first_character_index, truth.last_character_index
                inter = max(0, min(my_end, end) - max(my_start, start))
                union = ((my_end - my_start) + (end - start)) - inter
                IoU = inter / union
                if IoU >= 0.05:
                    for r in recall:
                        if r >= rec + 1:
                            recall[r] += 1
                    break

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