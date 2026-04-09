# SpecGuard

AI-powered system to detect documentation drift and validate claims using code and LLM reasoning.

## Features

- Regex + AI claim extraction from markdown documentation
- Natural-language and markdown-table claim detection
- Python code parsing for constants, typed assignments, config dictionaries, dataclasses, and `os.getenv` defaults
- File and line-aware reporting for both docs and code
- AI validation to judge whether mismatches reflect real drift
- GitHub pull request comments through GitHub Actions
- Stable PR comment updates instead of posting a new comment every run

## Project Layout

```text
specguard/
  specguard/
    __init__.py
    extractor.py
    code_parser.py
    comparator.py
    ai_validator.py
    scanner.py
    reporter.py
  cli.py
  requirements.txt
  README.md
  .github/workflows/specguard.yml
  examples/
    sample.md
    sample.py
  tests/
```

## How It Works

1. SpecGuard extracts claims like `Retries: 3`, markdown table values, and simple natural-language statements from documentation.
2. It optionally falls back to OpenAI-powered extraction if regex-based extraction finds nothing useful.
3. It parses Python files and collects configuration-like values such as uppercase constants, typed defaults, dataclass fields, dictionary-backed settings, and `os.getenv(..., default)` fallbacks.
4. It compares documentation claims to code constants with light alias matching for keys such as `retry_count` and `retries`.
5. For each mismatch, it asks OpenAI whether the documentation claim matches the code behavior and includes a confidence score.
6. It formats the results for both local CLI output and GitHub pull request comments, including doc and code locations.

## Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the CLI:

```bash
python cli.py --doc examples/sample.md --code examples/
```

Optionally enable fallback LLM extraction:

```bash
python cli.py --doc examples/sample.md --code examples/ --use-llm-extraction
```

Write a GitHub-ready markdown report to disk:

```bash
python cli.py --doc examples/sample.md --code examples/ --github-output specguard_report.md
```

## OpenAI Configuration

Set your API key before using AI validation:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

If the API key is missing, SpecGuard fails gracefully and marks AI validation as uncertain instead of crashing.

## Example

`examples/sample.md`

```md
Retries: 3
Timeout: 5
```

`examples/sample.py`

```python
RETRIES = 2
TIMEOUT = 5
```

This produces a drift report because `Retries` differs between documentation and code.

## GitHub Action

The included workflow runs on `pull_request`, executes SpecGuard, saves the markdown report, and updates a single persistent pull request comment with `actions/github-script`.

Workflow behavior:

- Runs `python cli.py --doc README.md --code . --github-output specguard_report.md`
- Captures non-zero exit status without stopping the workflow immediately
- Finds the existing SpecGuard comment marker and updates it, or creates a new comment if one does not exist
- Fails the workflow after commenting when drift is detected

This keeps pull requests tidy while still surfacing every new report.

## Running Tests

```bash
python -m unittest discover -s tests
```

## Notes

- The parser is strongest on Python configuration patterns and literal defaults.
- Natural-language extraction is heuristic-based, so OpenAI fallback remains useful for richer prose.
- AI validation is designed as an intelligent helper, not a replacement for deterministic comparison.
