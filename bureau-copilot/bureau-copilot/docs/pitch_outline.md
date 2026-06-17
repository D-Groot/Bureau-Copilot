# Pitch Outline — Bureaucracy Copilot
(15 slides max — this is structured at 11 so you have buffer)

---

**Slide 1 — Title**
Bureaucracy Copilot
"The agent that knows which form fields can silently end your future."
Team name | FAr Away Hackathon | Theme: AI Agents & Automation

---

**Slide 2 — The real problem (lead with the human cost)**
- Every year, eligible students miss scholarships, certificates, or exam
  registrations — not from lack of merit, but from ONE wrong field.
- Category, income bracket, domicile proof, document number formats:
  get it subtly wrong, find out weeks later, too late to fix.
- This isn't hypothetical — say it happened in your own family's
  research into AME CET / scholarship paperwork.

---

**Slide 3 — Why existing tools don't solve this**
- Generic "AI form fillers" just autocomplete — they don't know which
  fields are dangerous.
- Government helplines are slow, often inaccessible in regional language.
- People are left guessing on the fields that matter most.

---

**Slide 4 — Our agent: not a wrapper, a 4-step loop**
PERCEIVE → ASSESS → DECIDE → ACT
- Each step is a separate, inspectable reasoning step.
- The agent decides *what it needs to ask*, not a fixed checklist.

---

**Slide 5 — Step 1+2: Perceive & Assess**
- Reads raw/messy form text.
- Scores every field: RED (high rejection risk) / YELLOW (ambiguous) /
  GREEN (safe).
- Explains *why* in plain language — this is the "aha" most tools skip.

---

**Slide 6 — Step 3: Decide**
- Out of 20 fields, maybe only 4-5 are actually risky.
- The agent only asks about those — respecting the user's time and
  avoiding the "100 question form" fatigue that causes abandonment.

---

**Slide 7 — Step 4: Act**
- Produces a filled draft.
- Explains the riskiest fields in plain English AND Telugu — built for
  the people actually filling these forms, not just English-fluent users.

---

**Slide 8 — Live Demo**
[Run `python demo.py samples/scholarship_form.txt` live here]
Walk through: parsing → red/yellow/green table → 2-3 questions →
filled draft → bilingual explanation.

---

**Slide 9 — Why this scales beyond one form**
- Same loop works on: income certificates, caste certificates, exam
  registration forms, bank KYC — anything text-based.
- No hardcoded form structure — it reasons over whatever it's given.

---

**Slide 10 — What's next**
- OCR so people can photograph physical forms.
- Per-form-type risk knowledge base that sharpens with use.
- WhatsApp front-end — closer to where our actual users already are.

---

**Slide 11 — Close**
"We didn't build an agent that fills forms faster.
We built one that knows which mistakes actually cost people their future —
and asks about those, in their own language."
Thank you. [Repo link] [Team names]

---

## Tips for the next 10 minutes
- Skip slide design polish — a clean, consistent font and 2-3 colors
  (use the red/yellow/green from the demo itself) is enough.
- Screenshot the actual CLI output (colored risk table) and paste it
  into slide 5/6 as a static image in case live demo has any hiccup.
- Practice saying the Slide 2 line out loud once — that's your hook.
