import os
import tempfile
import shutil
import ast
import requests
from radon.complexity import cc_visit
from radon.metrics import mi_visit
from git import Repo

FOUNDRY_IQ_ENDPOINT = os.getenv("FOUNDRY_IQ_ENDPOINT", "")
FOUNDRY_IQ_KEY = os.getenv("FOUNDRY_IQ_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SEVERITY_THRESHOLDS = {
    "critical": 20,
    "high": 10,
    "medium": 5,
    "low": 0,
}

def get_severity(complexity: int) -> str:
    if complexity >= SEVERITY_THRESHOLDS["critical"]:
        return "critical"
    elif complexity >= SEVERITY_THRESHOLDS["high"]:
        return "high"
    elif complexity >= SEVERITY_THRESHOLDS["medium"]:
        return "medium"
    return "low"

def get_maintainability(code: str) -> float:
    try:
        score = mi_visit(code, multi=True)
        return round(score, 1)
    except Exception:
        return 0.0

def count_undocumented(code: str) -> int:
    try:
        tree = ast.parse(code)
        undoc = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not (ast.get_docstring(node)):
                    undoc += 1
        return undoc
    except Exception:
        return 0

def get_ai_recommendation(filename: str, complexity: int, undocumented: int, code_snippet: str) -> dict:
    if ANTHROPIC_API_KEY:
        return get_claude_recommendation(filename, complexity, undocumented, code_snippet)
    return get_fallback_recommendation(filename, complexity, undocumented)

def get_claude_recommendation(filename: str, complexity: int, undocumented: int, code_snippet: str) -> dict:
    prompt = f"""You are a senior software engineer helping reduce developer burnout by identifying tech debt.

Analyse this code file:
- Filename: {filename}
- Cyclomatic complexity score: {complexity}
- Undocumented functions/classes: {undocumented}

Code (first 800 chars):
{code_snippet[:800]}

Respond in JSON with exactly these fields:
{{
  "summary": "one sentence describing the main problem",
  "fix_plan": ["step 1", "step 2", "step 3"],
  "effort": "low|medium|high",
  "burnout_reason": "one sentence on why this causes burnout",
  "citation": "best practice or pattern name that applies"
}}"""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=20
        )
        data = response.json()
        text = data["content"][0]["text"]
        import json, re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return get_fallback_recommendation(filename, complexity, undocumented)

def get_fallback_recommendation(filename: str, complexity: int, undocumented: int) -> dict:
    if complexity >= 20:
        summary = "Extremely high complexity — this file is a prime burnout source."
        fix_plan = [
            "Break large functions into smaller, single-responsibility units",
            "Introduce early returns to reduce nesting depth",
            "Add unit tests before refactoring to catch regressions"
        ]
        effort = "high"
        burnout_reason = "High complexity means every change risks breaking something, creating constant anxiety."
        citation = "Single Responsibility Principle (SOLID)"
    elif complexity >= 10:
        summary = "High complexity with maintainability risk — needs attention soon."
        fix_plan = [
            "Extract repeated logic into helper functions",
            "Reduce conditional nesting with guard clauses",
            "Add docstrings to all public functions"
        ]
        effort = "medium"
        burnout_reason = "Undocumented complex code slows onboarding and causes debugging fatigue."
        citation = "Clean Code — Robert C. Martin"
    elif undocumented > 3:
        summary = "Low complexity but poorly documented — hidden time drain."
        fix_plan = [
            f"Add docstrings to the {undocumented} undocumented functions",
            "Add type hints to function signatures",
            "Write a module-level docstring explaining purpose"
        ]
        effort = "low"
        burnout_reason = "Undocumented code forces developers to reverse-engineer intent, wasting mental energy."
        citation = "Google Python Style Guide — Docstrings"
    else:
        summary = "This file looks healthy — low priority for refactoring."
        fix_plan = ["Maintain current standards", "Consider adding type hints if missing"]
        effort = "low"
        burnout_reason = "Well-structured code reduces cognitive load and context switching."
        citation = "PEP 8 — Style Guide for Python Code"

    return {
        "summary": summary,
        "fix_plan": fix_plan,
        "effort": effort,
        "burnout_reason": burnout_reason,
        "citation": citation
    }

def analyse_code(code: str, filename: str = "snippet.py") -> list:
    results = []
    try:
        blocks = cc_visit(code)
        total_complexity = sum(b.complexity for b in blocks) if blocks else 1
        maintainability = get_maintainability(code)
        undocumented = count_undocumented(code)
        severity = get_severity(total_complexity)
        burnout_score = calculate_burnout_score(total_complexity, undocumented)
        recommendation = get_ai_recommendation(filename, total_complexity, undocumented, code)

        hotspots = []
        for block in sorted(blocks, key=lambda b: b.complexity, reverse=True)[:5]:
            hotspots.append({
                "name": block.name,
                "complexity": block.complexity,
                "line": block.lineno,
                "type": block.letter
            })

        results.append({
            "filename": filename,
            "complexity": total_complexity,
            "maintainability": maintainability,
            "undocumented": undocumented,
            "severity": severity,
            "burnout_score": burnout_score,
            "hotspots": hotspots,
            "recommendation": recommendation
        })
    except Exception as e:
        results.append({
            "filename": filename,
            "complexity": 0,
            "maintainability": 0,
            "undocumented": 0,
            "severity": "low",
            "hotspots": [],
            "recommendation": get_fallback_recommendation(filename, 0, 0),
            "error": str(e)
        })
    return results

def analyse_repo(url: str) -> list:
    tmpdir = tempfile.mkdtemp()
    try:
        Repo.clone_from(url, tmpdir, depth=1)
        results = []
        for root, dirs, files in os.walk(tmpdir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__' and d != 'node_modules']
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, tmpdir)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    if len(code.strip()) < 10:
                        continue
                    file_results = analyse_code(code, rel_path)
                    results.extend(file_results)
                except Exception:
                    continue
            if len(results) >= 20:
                break
        results.sort(key=lambda r: r['complexity'], reverse=True)
        return results[:15]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def calculate_burnout_score(complexity, undocumented):
    score = complexity * 2 + undocumented * 3
    return min(score, 100)
    
