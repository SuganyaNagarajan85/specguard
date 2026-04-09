# SpecGuard

SpecGuard detects documentation drift by comparing claims in markdown docs against values and defaults inferred from Python code and configuration. It is aimed at engineering teams that want docs to remain operationally accurate as code changes, with optional OpenAI-based validation to help reduce false positives when a mismatch needs more context than a direct value comparison can provide.

## Why SpecGuard

Documentation drift usually starts small: a retry count changes, a timeout default moves, or a feature flag no longer matches the implementation. Those inconsistencies are easy to miss in review and expensive to discover later. SpecGuard helps surface them early by checking what the docs claim against what the code actually defines.

## Features

- Extracts claims from markdown using regex-based parsing
- Detects claims in simple natural-language sentences and markdown tables
- Parses Python configuration patterns including module-level constants, typed assignments, config dictionaries, dataclass-style config classes, and `os.getenv(..., default)` fallbacks
- Produces file and line-aware reports for both docs and code
- Optionally uses OpenAI to validate mismatches with a confidence score and explanation
- Supports CLI usage for local checks and CI integration
- Can format results as GitHub-friendly pull request comments

## How It Works

1. Read a markdown document and extract structured claims such as `Retries: 3` or `The retry count defaults to 4`.
2. Parse Python files to collect comparable configuration values and defaults.
3. Match documentation claims to code-derived values.
4. Flag mismatches and missing code matches.
5. Optionally send mismatches to OpenAI for a second-pass validation.
6. Render results for the terminal or a GitHub-compatible markdown comment.

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

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run against the included example:

```bash
python cli.py --doc examples/sample.md --code examples/
```

Write a GitHub-ready markdown report:

```bash
python cli.py --doc examples/sample.md --code examples/ --github-output specguard_report.md
```

Enable LLM fallback extraction when needed:

```bash
python cli.py --doc examples/sample.md --code examples/ --use-llm-extraction
```

## OpenAI Configuration

OpenAI is optional.

If `OPENAI_API_KEY` is set, SpecGuard can:

- Fall back to LLM-based claim extraction when rule-based extraction is insufficient
- Validate mismatches with a confidence score and short explanation

Configure it with:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

If the API key is not set, SpecGuard still runs and marks AI validation as unavailable instead of failing.

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

In this example, `timeout` matches, while `retries` is flagged because the documented value differs from the code value.

## Sample Output

```text
SpecGuard detected documentation drift:

- retries mismatch:
  Doc: 3 (sample.md:1)
  Code: 2 (sample.py:1)
  AI Verdict: Uncertain (Confidence: 0%)
  Reason: OPENAI_API_KEY is not set; skipping AI validation.
```

## Good Fit For

- Teams that treat documentation as part of the release surface
- Python services and tools with configuration-heavy behavior
- Repositories that want a lightweight doc-versus-code check in CI
- Pull request workflows where stale docs should be caught during review

## Limitations

- Python support is focused on common configuration patterns, not full runtime behavior
- Documentation extraction is heuristic-based and works best on explicit, structured claims
- AI validation is assistive, not authoritative
- Non-Python languages are not currently parsed

## Roadmap

- Broader parsing support for additional Python patterns and frameworks
- Better extraction for more free-form technical prose
- Smarter key aliasing and comparison logic
- Expanded machine-readable outputs for downstream tooling
- More robust pull request comment workflows

## Running Tests

```bash
python -m unittest discover -s tests
```
