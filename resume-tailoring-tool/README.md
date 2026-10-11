# Resume Tailoring Tool

A Python CLI that ranks master-resume content against a job description using transparent weighted keyword matching. Built by [Alekhya Tadikonda](https://github.com/alekhya-afk).

## Run the demo

Requires Python 3.10+. No third-party dependencies or API keys.

```bash
python3 resume_filter.py
python3 -m unittest discover -s tests -v
```

Run these commands from the extracted project folder. The included inputs are fictional. See [sample tailored resume](examples/output/tailored_resume.txt) and [sample report](examples/output/job_match_report.txt).

## Features

- Structured text parsing and whole-term, case-insensitive skill matching with aliases.
- Weighted ranking of skills, projects, experience, and bullets.
- Selection of up to three projects, two experience entries, and one additional experience entry.
- Up to three selected bullets per entry, retaining their original wording and order.
- Text and JSON reports with matching evidence and missing skills.
- Original content retained when no entries in a section match supported keywords.

## Scoring

| Job section | Points per matching line |
| --- | ---: |
| Qualifications, Requirements, Skills | 3 |
| Responsibilities, Preferred Qualifications | 2 |
| Summary and other sections | 1 |

A skill mentioned in Summary, Responsibilities, and Qualifications receives 6 points. Each line counts once per skill. Entry and bullet scores add the weights of their matched skills.

The match percentage measures weighted coverage of detected job skills in the **master resume**, including project and experience evidence. It is not an ATS score, a measurement of the final selected resume, or a hiring prediction. No detected skills produces 0%, meaning coverage cannot be assessed with the current vocabulary.

## Input format

Use headings ending in a colon, one skill per line, and one bullet per line:

```text
Skills:
Python
Git

Projects:
Motion Analyzer | Python, NumPy
Processed experimental CSV files using Python.

Experience:
Student Assistant | Example Department | 2025 - Present
Automated file organization using Python.
```

Use exact scored section names: `Projects`, `Experience`, `Additional Experience`, and `Skills`. Other sections are copied. Experience headers require a date in their final pipe-separated field. Project headers should not end with a period. Ordinary lines ending with a colon become headings.

Job headings such as `Summary:`, `Responsibilities:`, and `Qualifications:` activate section weights. Plain job text is supported with weight 1.

## Personal files

Keep personal inputs in the ignored `private/` folder:

```bash
python3 resume_filter.py --resume private/resume.txt --job private/job.txt --output-dir output --bullet-limit 3
```

Customize `DEFAULT_SKILLS`, `SKILL_ALIASES`, and `DEFAULT_SELECTION_LIMITS` in the source.

## Outputs

| File | Contents |
| --- | --- |
| `output/tailored_resume.txt` | Selected resume content |
| `output/job_match_report.txt` | Readable matching explanation |
| `output/job_match_report.json` | Scores, evidence, entries, and resume |
| `output/rewrite_requests.json` | Original bullets and future model instructions |

This version does not call an AI model or rewrite bullets. PDF, Word, and frontend support are future improvements.

## Tests and limitations

Nine tests cover aliases, boundaries, weights, bullet ranking, exports, preservation of original bullets, no-match behavior, and invalid inputs. GitHub Actions is configured to test Python 3.10-3.13 after uploading.

A fixed vocabulary can miss synonyms and context or match negated statements. Review output before applying. No-match sections retain original content and may exceed selection limits. The program does not verify resume claims.

## Files

`resume_filter.py` contains the CLI and reusable pipeline; `tests/` contains automated checks; `examples/output/` contains reproducible results; `.github/workflows/tests.yml` configures CI. See [GitHub setup](GITHUB_SETUP.md) for upload instructions.
