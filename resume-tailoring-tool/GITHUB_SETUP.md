# Upload to GitHub

1. Unzip the archive on your Mac.
2. Sign in at https://github.com/new with your `alekhya-afk` account.
3. Name the repository `resume-tailoring-tool`.
4. Description: `Python CLI for resume tailoring using explainable weighted keyword matching.`
5. Choose Public for recruiter access. Leave automatic README creation off; one is included.
6. Create the repository and select **Add file → Upload files**.
7. Upload the contents of the extracted project folder, including subfolders. Do not upload the ZIP or an extra enclosing folder.
8. Press Command + Shift + Period in Finder to show hidden files. Include `.gitignore` and `.github/workflows/tests.yml`. If they do not upload, create each through **Add file → Create new file** using its exact path and included contents.
9. Commit with `Add resume tailoring tool and tests`.
10. Check the Actions tab for test results and pin the repository on your profile.

Suggested topics: `python`, `resume`, `automation`, `cli`, `keyword-matching`.

## Demo

Open Terminal in the project folder:

```bash
python3 -m unittest discover -s tests -v
python3 resume_filter.py
```

Show the fictional inputs, tailored resume, and scoring report. Explain how qualification weights influence ranking and how bullets retain original facts. Keep personal inputs in the ignored `private/` folder.
