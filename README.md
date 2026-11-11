# adversarial-resume-review

A skill for stress-testing an engineering resume (any discipline): a **mock ATS parse**, then an **adversarial reviewer panel** of different models role-playing interviewers at different kinds of employers, then fix-and-re-run loops.

- `SKILL.md`: the full procedure (fact-gathering, bullet formula, ATS check, reviewer personas and prompt template, synthesis, integrity guardrails).
- `scripts/mock_ats.py`: parses resume text (from `pdftotext -layout`), reports what an ATS extracts, and scores keyword coverage.
- `scripts/jd_profiles.json`: starter job-keyword profiles (software, data, DevOps/SRE, embedded, power systems, mechanical, civil, bilingual). Extend as needed.

```bash
pdftotext -layout resume.pdf resume.txt
python3 scripts/mock_ats.py resume.txt --jd-profiles scripts/jd_profiles.json
python3 scripts/mock_ats.py resume.txt --jd-text job_posting.txt
```

The scorer is an approximation of commercial ATS keyword matching, not a reproduction of any vendor's algorithm. Never add skills or numbers that aren't true.
