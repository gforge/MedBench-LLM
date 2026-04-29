"""Upload LLM-generated summaries to the MedBench Platform.

Scans data/output/{specialty}/Summary_4_*.txt files, maps each to a
chartTranslationId via allData.json, and calls uploadLLMGeneratedSummaries.

Usage:
    python src/upload_summaries.py --url http://localhost:4000 --token <jwt> --specialty Medicine
    python src/upload_summaries.py --url http://localhost:4000 --email admin@x.com --specialty all
    # reads MEDBENCH_DATA_SERVER_API (or MEDBENCH_URL), MEDBENCH_TOKEN
    # or MEDBENCH_EMAIL/MEDBENCH_PASSWORD from env
"""

import argparse
import getpass
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

UPLOAD_MUTATION = """
mutation UploadSummaries($summaries: [SummaryInput!]!) {
  uploadLLMGeneratedSummaries(summaries: $summaries) {
    id
    chartTranslationId
    generatedBy
  }
}
"""

LOGIN_MUTATION = """
mutation Login($email: String!, $password: String!) {
  login(email: $email, password: $password) {
    accessToken
  }
}
"""


def graphql_request(url: str, query: str, variables: dict, token: str | None = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
    if "errors" in body:
        raise RuntimeError(f"GraphQL error: {body['errors']}")
    return body["data"]


def get_token(url: str, email: str, password: str) -> str:
    data = graphql_request(url, LOGIN_MUTATION, {"email": email, "password": password})
    return data["login"]["accessToken"]


def build_chart_index(alldata_path: Path) -> dict[tuple[str, str, str], str]:
    """Return {(specialty, case_id, language): chartTranslationId}."""
    with open(alldata_path, encoding="utf-8") as f:
        cases = json.load(f)
    index: dict[tuple[str, str, str], str] = {}
    for case in cases:
        for chart in case.get("charts", []):
            key = (chart["specialty"], chart["name"], chart["language"])
            index[key] = chart["id"]
    return index


def parse_summary_filename(path: Path) -> tuple[str, str, str] | None:
    """Parse Summary_4_{case_id}@{language}@{generatedBy}.txt → (case_id, language, generatedBy).

    Returns None if the filename does not match the expected pattern.
    """
    name = path.stem  # strip .txt
    if not name.startswith("Summary_4_"):
        return None
    rest = name[len("Summary_4_"):]
    parts = rest.split("@")
    if len(parts) < 3:
        return None
    case_id = parts[0]
    language = parts[1]
    generated_by = "@".join(parts[2:])
    if not generated_by.startswith("$"):
        return None
    return case_id, language, generated_by


def collect_summaries(output_dir: Path, specialty: str, chart_index: dict) -> list[dict]:
    summaries = []
    skipped = []
    for txt_file in sorted(output_dir.glob("Summary_4_*.txt")):
        parsed = parse_summary_filename(txt_file)
        if not parsed:
            print(f"  [skip] Unrecognised filename: {txt_file.name}")
            continue
        case_id, language, generated_by = parsed
        key = (specialty, case_id, language)
        chart_id = chart_index.get(key)
        if not chart_id:
            skipped.append(f"  [skip] No chartTranslationId for {key}")
            continue
        text = txt_file.read_text(encoding="utf-8").strip()
        if len(text) < 50:
            skipped.append(f"  [skip] Text too short (<50 chars): {txt_file.name}")
            continue
        summaries.append({"chartTranslationId": chart_id, "generatedBy": generated_by, "text": text})
    for msg in skipped:
        print(msg)
    return summaries


def upload_in_batches(url: str, token: str, summaries: list[dict], batch_size: int = 50) -> int:
    uploaded = 0
    for i in range(0, len(summaries), batch_size):
        batch = summaries[i : i + batch_size]
        result = graphql_request(url, UPLOAD_MUTATION, {"summaries": batch}, token=token)
        uploaded += len(result["uploadLLMGeneratedSummaries"])
        print(f"  Uploaded batch {i // batch_size + 1}: {len(batch)} summaries")
    return uploaded


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload LLM summaries to MedBench Platform")
    parser.add_argument(
        "--url",
        default=os.environ.get("MEDBENCH_DATA_SERVER_API")
        or os.environ.get("MEDBENCH_URL", "http://localhost:4000/graphql"),
    )
    parser.add_argument("--token", default=os.environ.get("MEDBENCH_TOKEN"))
    parser.add_argument("--email", default=os.environ.get("MEDBENCH_EMAIL"))
    parser.add_argument(
        "--password",
        default=os.environ.get("MEDBENCH_PASSWORD"),
        help="Password for login; if omitted the script prompts securely when --email is provided",
    )
    parser.add_argument("--specialty", default="Medicine", help="Specialty subfolder (or 'all' for all subfolders)")
    parser.add_argument(
        "--alldata",
        default=str(Path(__file__).parent.parent / "data" / "output" / "allData.json"),
        help="Path to allData.json exported from the Platform",
    )
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()

    token = args.token
    if not token:
        if not args.email:
            parser.error("Provide --token or --email (or set MEDBENCH_TOKEN / MEDBENCH_EMAIL env vars)")
        if not args.password:
            args.password = getpass.getpass(f"Password for {args.email}: ")
        print(f"Logging in as {args.email}...")
        token = get_token(args.url, args.email, args.password)
        print("Login successful.")

    alldata_path = Path(args.alldata)
    if not alldata_path.exists():
        parser.error(f"allData.json not found at {alldata_path}. Run download_platform_charts.py first.")

    print(f"Loading chart index from {alldata_path}...")
    chart_index = build_chart_index(alldata_path)
    print(f"Loaded {len(chart_index)} chart translations.")

    output_base = Path(__file__).parent.parent / "data" / "output"

    specialties: list[str]
    if args.specialty.lower() == "all":
        specialties = [d.name for d in output_base.iterdir() if d.is_dir()]
    else:
        specialties = [args.specialty]

    total_uploaded = 0
    for specialty in specialties:
        output_dir = output_base / specialty
        if not output_dir.exists():
            print(f"[{specialty}] Output directory not found, skipping.")
            continue
        print(f"\n[{specialty}] Scanning {output_dir}...")
        summaries = collect_summaries(output_dir, specialty, chart_index)
        if not summaries:
            print(f"[{specialty}] No uploadable summaries found.")
            continue
        print(f"[{specialty}] Uploading {len(summaries)} summaries...")
        n = upload_in_batches(args.url, token, summaries, batch_size=args.batch_size)
        total_uploaded += n
        print(f"[{specialty}] Done: {n} uploaded.")

    print(f"\nTotal uploaded: {total_uploaded}")


if __name__ == "__main__":
    main()
