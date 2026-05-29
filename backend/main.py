import os
import tempfile
import shutil
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from analyser import analyse_code, analyse_repo

app = FastAPI(title="BurnoutLess API")

app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
def root():
    return FileResponse("../frontend/index.html")

class SnippetRequest(BaseModel):
    code: str
    filename: str = "snippet.py"

class RepoRequest(BaseModel):
    url: str

@app.post("/analyse/snippet")
def analyse_snippet(req: SnippetRequest):
    try:
        results = analyse_code(req.code, req.filename)
        return {"status": "ok", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyse/repo")
def analyse_repo_url(req: RepoRequest):
    try:
        results = analyse_repo(req.url)
        return {"status": "ok", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
