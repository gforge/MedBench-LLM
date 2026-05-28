import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helpers.read_data import read_json_file
from helpers.read_prompt import read_dual_prompt
from helpers.types import parse_language_input


class IcelandicBasicPromptTests(unittest.TestCase):
    def test_parse_language_input_accepts_icelandic(self) -> None:
        self.assertEqual(parse_language_input("Icelandic"), ("Icelandic", "plain"))
        self.assertEqual(parse_language_input("Icelandic-clinical"), ("Icelandic", "clinical"))

    def test_reads_icelandic_basic_prompts(self) -> None:
        prompt_path = Path(__file__).resolve().parents[1] / "src" / "prompts" / "basic" / "prompts"

        prompt = read_dual_prompt("basic", prompt_path=prompt_path, language="Icelandic")

        self.assertIn("útskriftarnótur", prompt.system)
        self.assertIn("{nótur}", prompt.human)

    def test_reads_icelandic_case_and_note_helpers(self) -> None:
        case_path = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "processed"
            / "markdown"
            / "markdown_Orthopaedics_Case 1_Icelandic.json"
        )

        case = read_json_file(case_path)

        self.assertEqual(case.language, "Icelandic")
        self.assertTrue(case.progress_notes)
        self.assertTrue(case.surgery)


if __name__ == "__main__":
    unittest.main()
