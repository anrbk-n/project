from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pipelines.v_download import run_pipeline
from pipelines.subtitles import transcribe_youtube_with_punctuation

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def form_page(request: Request):
    return templates.TemplateResponse("form.html", {"request": request, "video": False})


@app.post("/", response_class=HTMLResponse)
def handle_form(request: Request, url: str = Form(...)):
    run_pipeline(url)
    transcribe_youtube_with_punctuation(url)
    return templates.TemplateResponse("form.html", {"request": request, "video": True})


@app.get("/video/")
def get_video():
    return FileResponse("dada.mp4", media_type="video/mp4", filename="video.mp4")


@app.get("/subtitles/")
def get_subtitles():
    return FileResponse("transcript_punctuated.txt", media_type="text/plain", filename="subtitles.txt")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
