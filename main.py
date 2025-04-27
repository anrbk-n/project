from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from pipelines.subtitles import transcribe_youtube_with_punctuation
from pipelines.rag import generate_summary, ask_question
from pipelines.v_download import run_pipeline

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

session_data = {
    "url": None,
    "subtitles": None,
    "dialogue": [],
    "video_ready": False
}

def format_summary(summary: str, chunk_size: int = 3) -> str:
    summary = summary.replace('?', '?.').replace('!', '!.')
    sentences = summary.split('.')
    paragraphs = []
    for i in range(0, len(sentences), chunk_size):
        chunk = sentences[i:i+chunk_size]
        paragraph = '. '.join(s.strip() for s in chunk if s.strip())
        if paragraph:
            paragraphs.append(f"<p>{paragraph}.</p>")
    return "\n".join(paragraphs)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/process", response_class=HTMLResponse)
async def process_link(request: Request, url: str = Form(...)):
    subtitles = transcribe_youtube_with_punctuation(url)
    if subtitles:
        session_data["url"] = url
        session_data["subtitles"] = subtitles
        session_data["dialogue"] = []
        session_data["video_ready"] = False
        return RedirectResponse(url="/choose", status_code=303)
    else:
        return templates.TemplateResponse("form.html", {"request": request, "error": True})

@app.get("/choose", response_class=HTMLResponse)
async def choose(request: Request):
    return templates.TemplateResponse("choose.html", {"request": request})

@app.get("/ask", response_class=HTMLResponse)
async def ask_page(request: Request):
    dialogue = list(reversed(session_data["dialogue"]))  # Новые сверху
    return templates.TemplateResponse("ask.html", {"request": request, "dialogue": dialogue})

@app.post("/ask", response_class=HTMLResponse)
async def ask_submit(request: Request, question: str = Form(...)):
    answer = ask_question(question)
    session_data["dialogue"].append((question, answer))
    dialogue = list(reversed(session_data["dialogue"]))
    return templates.TemplateResponse("ask.html", {"request": request, "dialogue": dialogue})

@app.get("/summary", response_class=HTMLResponse)
async def summary_page(request: Request):
    raw_summary = generate_summary()
    summary = format_summary(raw_summary)
    return templates.TemplateResponse("summary.html", {"request": request, "summary": summary})

@app.get("/download")
async def download():
    url = session_data.get("url")
    if not url:
        return RedirectResponse(url="/choose", status_code=303)

    if not session_data["video_ready"]:
        run_pipeline(url)
        session_data["video_ready"] = True

    return RedirectResponse(url="/watch", status_code=303)

@app.get("/watch", response_class=HTMLResponse)
async def watch(request: Request):
    if not os.path.exists("download_video.mp4"):
        session_data["video_ready"] = False
        return RedirectResponse(url="/choose", status_code=303)

    return templates.TemplateResponse("watch.html", {"request": request})
@app.post("/clear_chat")
async def clear_chat():
    session_data["dialogue"] = []
    return {"status": "cleared"}

@app.get("/video")
async def get_video():
    if os.path.exists("download_video.mp4"):
        return FileResponse("download_video.mp4", media_type="video/mp4")
    else:
        return {"error": "Video not found"}
@app.get("/progress")
async def progress():
    if os.path.exists("progress.json"):
        with open("progress.json", "r") as f:
            return json.load(f)
    return {"downloaded_bytes": 0, "total_bytes": 1}  


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
