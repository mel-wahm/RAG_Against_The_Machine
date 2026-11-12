from src.models import (
    RagDataset,
    StudentSearchResults,
    MinimalSource,
    AnsweredQuestion,
    MinimalSearchResults,
    UnansweredQuestion,
)
import json
from pathlib import Path


class Evaluator:
    def __init__(self, student_search_results_path: str, dataset_path: str):
        self.student_search_results_path = student_search_results_path
        self.dataset_path = dataset_path

    def calculate_iou(
        self, first_chunk: MinimalSource, second_chunk: MinimalSource
    ) -> float:
        if first_chunk.file_path != second_chunk.file_path:
            return 0.0
        f_start, f_end = (
            first_chunk.first_character_index,
            first_chunk.last_character_index,
        )
        s_start, s_end = (
            second_chunk.first_character_index,
            second_chunk.last_character_index,
        )
        inter = max(0, min(f_end, s_end) - max(f_start, s_start))
        union = (f_end - f_start) + (s_end - s_start) - inter
        if not union:
            return 0.0
        return inter / union

    def calculate_recall(
        self,
        r: int,
        student_answers: list[MinimalSearchResults],
        ids: dict[str, AnsweredQuestion | UnansweredQuestion],
    ) -> float:
        recall = 0.0
        for answer in student_answers:
            truth = ids[answer.question_id]
            if not hasattr(truth, "sources"):
                continue
            truth_sources = truth.sources
            if not truth_sources:
                recall += 1.0
                continue
            for t in truth_sources:
                current = 0
                for a in answer.retrieved_sources[:r]:
                    rec = self.calculate_iou(a, t)
                    if rec >= 0.05:
                        current += 1
                        break
                recall += current / len(truth_sources)
        return recall

    def evaluate(self) -> None:
        ds_path = Path(self.dataset_path)
        sr_path = Path(self.student_search_results_path)

        if not ds_path.is_file():
            print(f"Error: Dataset file '{self.dataset_path}' "
                  "not found.")
            return
        if not sr_path.is_file():
            print(
                f"Error: Search results file "
                f"'{self.student_search_results_path}' not found."
            )
            return

        try:
            with open(ds_path) as f:
                dataset = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Dataset file '{self.dataset_path}' "
                  "contains invalid JSON.")
            return
        except Exception as e:
            print(f"Error reading dataset file: {e}")
            return

        try:
            with open(sr_path) as f:
                search_result = json.load(f)
        except json.JSONDecodeError:
            print(
                f"Error: File '{self.student_search_results_path}' "
                "contains invalid JSON."
            )
            return
        except Exception as e:
            print(f"Error reading search results file: {e}")
            return

        try:
            user_answers = StudentSearchResults.model_validate(
                search_result
            ).search_results
        except Exception as e:
            print(f"Error: Invalid student search results format: {e}")
            return

        try:
            dataset_answers = RagDataset.model_validate(dataset).rag_questions
        except Exception as e:
            print(f"Error: Invalid dataset format: {e}")
            return

        ids = {data.question_id: data for data in dataset_answers}
        total = len(dataset_answers)
        if total == 0:
            print("Error: The ground truth dataset contains 0 questions.")
            return

        recall = {
            1: 0.0,
            3: 0.0,
            5: 0.0,
            10: 0.0,
        }

        if not all(hasattr(truth, "sources") for truth in ids.values()):
            print(
                "Evaluation Error: You can't check your "
                "answers against Unansweredquestions, "
                "please use Answeredquestions dataset"
            )
            return

        for a in user_answers:
            # Report missing question IDs cleanly without an exception
            if a.question_id not in ids:
                print(
                    f'Error: Question with id "{a.question_id}" '
                    'not found in dataset.'
                )
                return

        for r in recall:
            recall[r] = self.calculate_recall(r, user_answers, ids)

        print()
        print("🎯 Evaluation Results")
        print("========================================")
        print()
        print(f"📊 Questions evaluated: {total}")
        for r in recall:
            print(
                f"📈 Recall@{r}: {(recall[r] / total):.3f}",
                f"    ({(recall[r] * 100 / total):.1f}%)",
            )
        print()
        print({f"recall{r}": recall[r] / total for r in sorted(recall)})
