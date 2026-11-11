---
name: adversarial-resume-review
description: Stress-test an engineering resume (any discipline) by running it through a mock ATS parser and a panel of adversarial reviewers role-playing different employers, then fix what they find. Use when asked to review, critique, score or harden a resume.
---

# Adversarial Resume Review

Use this procedure to harden a resume for any engineering role (software, data, DevOps/SRE, embedded, electrical, mechanical, civil, chemical and so on). It combines four things:

1. **Fact-gathering.** Pull every accomplishment from the candidate's real sources before rewriting anything.
2. **A mock ATS (applicant tracking system) parse.** Check what a resume parser extracts and how well keywords match target jobs.
3. **An adversarial reviewer panel.** Several models role-play skeptical interviewers at different kinds of employers.
4. **Fix and re-run loops.** Apply fixes and re-score until the remaining gaps are real experience gaps, not wording.

The rule throughout: **never invent facts or numbers.** Every metric must come from the candidate. Mark missing numbers `[X]` and ask for them.

---

## Step 0: Set the target and gather facts

Ask, or infer from context:
- **Target roles and level**, e.g. Senior IC, not management.
- **Target company types.** These matter more than anything else, because a big-tech bar and a utility bar give very different verdicts. Get a list such as:
  - big tech or FAANG
  - large incumbent in the candidate's industry (same size as the current employer)
  - startup or scale-up in the same domain
  - vendor or supplier to the industry
  - non-domain enterprise using the same stack
  - foreign-HQ subsidiary, if the candidate is multilingual
- **Sources of accomplishments:** the old resume, LinkedIn, an accomplishments doc (commit logs, Jira tickets, work journal), performance reviews.

Build one master list of accomplishments **with years attached**, so bullets can be placed under the right title and date range.

## Step 1: Draft the resume

**Structure**
- One page, unless the candidate has 10+ years of experience.
- Header: name, city and state, phone, email, LinkedIn, and site or portfolio if it's live.
- Optional summary line: required for multilingual or unusual-profile versions, and helpful for recruiter skims.
- Experience: list multiple titles under one employer heading with **bold titles** so promotions are visible.
- Education: graduation year is optional, and leaving it off is a trade-off (some screeners filter on it). One-line projects can go here.
- Skills: grouped lines, such as Languages, Cloud/Platforms, Tools, Practices, Domain, Spoken languages.

**Bullet formula: result first, then how**
`[Action verb] [what] that [measurable result], [how / tech]`
- Strong verbs: Built, Led, Architected, Cut, Scaled, Migrated, Designed, Delivered.
- Past tense throughout, one idea per bullet, and as few 3-line bullets as possible.
- Prefer before→after numbers: cost ($ and %), time (monthly→hourly), scale (3,000+ units), reliability (%), users (~20 engineers), team size.
- Explain internal names once in plain terms, for example "CYME grid-simulation models". Remove code names a recruiter won't know.
- Lead the most recent role with the strongest 1–2 bullets.
- Write IC leadership as "Technical lead on a ~N-person team, owning…" and "mentored", not "managed", unless the target is management.

**Variants:** create one per audience by copying the document. Typical variants are general and multilingual, and sometimes a domain-first version and a stack-first, low-jargon version.

## Step 2: Mock ATS parse

Export the resume to PDF, then extract the text the way an ATS would:

```bash
pdftotext -layout resume.pdf resume.txt
python3 scripts/mock_ats.py resume.txt --jd-profiles scripts/jd_profiles.json
# or against a real job posting:
python3 scripts/mock_ats.py resume.txt --jd-text job_posting.txt
```

The script reports:
- **Parsed profile:** name, email, phone, LinkedIn, location, sections, positions (title, employer, dates, bullet count), total years computed from dates, degree, graduation year, skills count.
- **Parse notes:** zero-width characters, missing graduation year, positions that didn't parse.
- **Quantified bullets:** bullets that contain a number or an outcome, out of the total.
- **Keyword match per job profile:** score out of 100 (70% required, 30% preferred), plus missing required and preferred terms. Synonyms are normalized; for example "github actions" counts as ci/cd.

Edit `scripts/jd_profiles.json` to add profiles for the target discipline. Starter profiles cover software, data, DevOps/SRE, embedded/firmware, electrical/power systems, mechanical, civil/structural and a multilingual role. **A real posting passed with `--jd-text` is always better than a generic profile.**

How to read the results:
- If parsing breaks (dates or titles not captured), fix the layout first: no tables or columns for core content, standard section names, and dates on the title line.
- **Only add a missing keyword if it's true.** Rephrase real work with the market term ("microservices", "distributed systems", "infrastructure as code"), or put it in Skills. Never add tools the candidate hasn't used.

## Step 3: Adversarial reviewer panel

Run several subagents **in parallel**, using **different models** for variety (for example Opus, Sonnet and Haiku). Give each a persona, a file path to the plain-text resume, and a strict output format. Tell them to be adversarial: find reasons to reject or down-level, with no flattery.

### Round A: generic bar (the hardest critics)

| Persona | Model | What they find |
|---|---|---|
| Hiring manager at a top-tier company | Sonnet | Level verdict, top 5 weaknesses with exact quotes, credibility red flags, 3 rewrites |
| Staff/principal "bar-raiser" | Opus | Senior vs mid-level, 5 claims to probe plus follow-up questions, unsupported skills, missing senior signals, single highest-leverage edit |
| Recruiter doing a 6-second skim | Haiku | What the eye catches first, pass/no, confusion points, formatting, summary line |

### Round B: the candidate's actual target companies

Pick 4–6 personas that match Step 0, for example:
- Hiring manager at a **large incumbent the same size as the current employer**
- VP Engineering at a **domain startup or scale-up**
- Engineering manager at a **vendor or supplier** to the industry
- Principal engineer at a **non-domain enterprise on the same stack**, who doesn't know the domain
- Bilingual hiring manager at a **foreign-HQ subsidiary**, using the multilingual version; also ask whether a local-format CV is expected (e.g. 職務経歴書, 履歴書, Lebenslauf)

**Prompt template for each reviewer:**
```
Role-play: you are <title> at <company type, with 2-4 example companies>, hiring a <level> <role>.
Review the resume critically and honestly (adversarial, not flattering). Use only the Read tool.
Read <path to plain-text resume>.
Respond in under 300 words:
1. Interview? Yes/No/Maybe, and the level you'd slot them at.
2. Fit score out of 10.
3. Top 3 strengths for YOUR company.
4. Top 3 concerns (quote exact phrases).
5. Two concrete edits (use only facts in the resume; mark wanted numbers [X]).
6. Two interview questions you'd ask.
```

### Synthesizing
- Put everything in **one table**: persona, model, interview, level, fit score.
- Pull out **consensus issues** (raised by 2 or more reviewers). These get fixed first.
- **Discard reviewer errors.** Models sometimes claim things that aren't in the resume, for example inventing a location conflict. Check each claim against the text.
- Split the findings into:
  1. **Wording fixes** you can make now.
  2. **Questions for the candidate:** missing numbers, team size, users, reliability %, what drove a result.
  3. **Interview prep:** the questions reviewers would ask. Give these to the candidate even when the resume is fine.
- Tell the candidate plainly when the remaining gap is **experience, not wording**. For example: "for big-tech Senior you'd need SLO/on-call/distributed-systems depth; rewording won't close that."

## Step 4: Fix, verify, re-run

1. Apply the fixes to **every variant**.
2. Re-export and confirm the **page count** is unchanged. If it overflows, trim bullets that wrap with a short last line, or shorten skills lines.
3. Re-run the mock ATS and show the score change (e.g. 62 → 68 → 79).
4. Re-run the panel if the changes were substantial, and compare verdicts and scores with the previous round.
5. Stop when the consensus issues are resolved and what's left needs real experience or data only the candidate has.

## Integrity guardrails
- Never fabricate metrics, tools, titles, dates or scope.
- If the resume's titles or dates differ from LinkedIn or other records, point it out. Background checks verify titles and dates, so tell the candidate to make them match.
- Inferred terms are fine only when they accurately describe the work, e.g. Helm + ArgoCD → Kubernetes only if it actually ran on a cluster. Ask when unsure.
- Keep the candidate's voice and their stated goal, for example IC rather than manager.

## Deliverables
- Updated resume variants: editable docs plus PDF exports.
- Mock ATS scores before and after.
- Panel summary table, consensus fixes, open questions and interview-prep list.
