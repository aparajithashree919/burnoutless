# BurnoutLess

> AI-powered tech debt triage agent — find what's burning your team out, and fix it first.

Built for the **Agents League Hackathon 2026** — Creative Apps track.

---

## The Problem

Developer burnout is at a crisis point in 2026. Over two-thirds of developers report mounting pressure to ship faster, while simultaneously inheriting complex, undocumented codebases that nobody dares touch. The result: anxiety, context-switching fatigue, and teams grinding to a halt on files that should have been refactored months ago.

The problem isn't the work — it's not knowing **where to start**.

## What BurnoutLess Does

BurnoutLess is an AI agent that scans your codebase and surfaces the exact files causing the most developer stress — ranked by severity, with a grounded, actionable fix plan for each.

**Input:** GitHub repo URL or pasted code snippet  
**Output:** A dashboard showing burnout hotspots ranked by severity, with cited fix recommendations powered by Microsoft Foundry IQ

### How it works

1. **Complexity scan** — uses `radon` to measure cyclomatic complexity and maintainability index per file
2. **Copilot analysis** — GitHub Copilot reviews flagged code for undocumented functions, risky patterns, and high-churn areas
3. **Foundry IQ grounding** — each recommendation is grounded in real best practice sources (Clean Code, SOLID principles, language style guides) — no hallucinations, cited answers
4. **Prioritised dashboard** — files ranked Critical → High → Medium → Low, each with a 3-step fix plan, effort estimate, and burnout risk explanation

## Microsoft IQ Layer

This project uses **Microsoft Foundry IQ** as its intelligence layer — connecting agent outputs to enterprise knowledge sources and delivering cited, grounded recommendations that reduce hallucination and build developer trust.

## Setup

```bash
git clone https://github.com/your-username/burnoutless
cd burnoutless
pip install -r requirements.txt

# Add your API key for AI-powered recommendations (optional — falls back gracefully)
export ANTHROPIC_API_KEY=your_key_here

# Run the server
cd backend
uvicorn main:app --reload
```

Then open http://localhost:8000 in your browser.

## Tech Stack

- **Backend:** Python, FastAPI, Radon, GitPython
- **Frontend:** Vanilla HTML/CSS/JS (no framework needed)
- **AI:** GitHub Copilot (code analysis) + Microsoft Foundry IQ (grounded recommendations)
- **IQ Layer:** Microsoft Foundry IQ

## Demo

[Watch the demo video →](#)

## Tracks

- Creative Apps (GitHub Copilot)
- Best Use of IQ Tools (Microsoft Foundry IQ)
- Hack for Good Award

## Team

Solo submission — built in 1 day for Agents League Hackathon 2026.
