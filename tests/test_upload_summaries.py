import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from upload_summaries import parse_summary_filename, resolve_upload_selection


class UploadSummarySelectionTests(unittest.TestCase):
    def test_parse_summary_filename_extracts_model_prompt_type_and_generated_by(self) -> None:
        path = Path("Summary_4_Case 1@original@$gpt-5.5_2026-04-24@temp=0.0@basic.txt")

        summary = parse_summary_filename(path, specialty="Orthopaedics")

        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary.case_id, "Case 1")
        self.assertEqual(summary.language, "original")
        self.assertEqual(summary.model_used, "gpt-5.5_2026-04-24@temp=0.0")
        self.assertEqual(summary.prompt_type, "basic")
        self.assertEqual(summary.generated_by, "$gpt-5.5_2026-04-24@temp=0.0@basic")
        self.assertEqual(summary.specialty, "Orthopaedics")

    def test_parse_summary_filename_rejects_missing_prompt_type(self) -> None:
        path = Path("Summary_4_Case 1@original@$gpt-5.5_2026-04-24.txt")

        summary = parse_summary_filename(path, specialty="Orthopaedics")

        self.assertIsNone(summary)

    def test_resolve_upload_selection_filters_multiple_metadata_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_base = Path(temp_dir)
            self._touch_summary(
                output_base,
                "Orthopaedics",
                "Summary_4_Case 1@original@$gpt-5.5_2026-04-24@temp=0.0@basic.txt",
            )
            self._touch_summary(
                output_base,
                "Orthopaedics",
                "Summary_4_Case 1@Swedish@$gpt-5.5_2026-04-24@temp=0.0@basic.txt",
            )
            self._touch_summary(
                output_base,
                "Orthopaedics",
                "Summary_4_Case 2@original@$gpt-5.5_2026-04-24@temp=0.0@reflection.txt",
            )
            self._touch_summary(
                output_base,
                "Orthopaedics",
                "Summary_4_Case 2@original@$gpt-5.2_2025-12-11@temp=0.0@basic.txt",
            )
            self._touch_summary(
                output_base,
                "Medicine",
                "Summary_4_Case 1@original@$gpt-5.5_2026-04-24@temp=0.0@basic.txt",
            )

            selected = resolve_upload_selection(
                output_base=output_base,
                specialty_arg="Orthopaedics",
                model_arg="gpt-5.5_2026-04-24@temp=0.0",
                language_arg="original,Swedish",
                prompt_type_arg="basic",
                case_arg="Case 1",
            )

        selected_names = sorted(summary.path.name for summary in selected)
        self.assertEqual(
            selected_names,
            [
                "Summary_4_Case 1@Swedish@$gpt-5.5_2026-04-24@temp=0.0@basic.txt",
                "Summary_4_Case 1@original@$gpt-5.5_2026-04-24@temp=0.0@basic.txt",
            ],
        )

    def test_resolve_upload_selection_accepts_all_filters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_base = Path(temp_dir)
            self._touch_summary(
                output_base,
                "Orthopaedics",
                "Summary_4_Case 1@original@$gpt-5.5_2026-04-24@temp=0.0@basic.txt",
            )
            self._touch_summary(
                output_base,
                "Medicine",
                "Summary_4_Case 2@Swedish@$gpt-5.2_2025-12-11@temp=0.0@reflection.txt",
            )

            selected = resolve_upload_selection(
                output_base=output_base,
                specialty_arg="all",
                model_arg="all",
                language_arg="all",
                prompt_type_arg="all",
                case_arg="all",
            )

        self.assertEqual(len(selected), 2)
        self.assertEqual({summary.specialty for summary in selected}, {"Medicine", "Orthopaedics"})

    @staticmethod
    def _touch_summary(output_base: Path, specialty: str, filename: str) -> None:
        specialty_dir = output_base / specialty
        specialty_dir.mkdir(parents=True, exist_ok=True)
        (specialty_dir / filename).write_text("summary text", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
