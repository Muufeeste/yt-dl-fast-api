import os
import random
import yt_dlp
import time
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from yt_dlp.postprocessor import FFmpegPostProcessor


download_path = os.environ.get('DOWNLOAD_PATH')
port = os.environ.get('PORT')
ffmpeg_location = os.environ.get('FFMPEG_LOCATION')


if download_path is None \
        or port is None\
        or ffmpeg_location is None:
    raise Exception('application environment not set properly')


FFmpegPostProcessor._ffmpeg_location.set(ffmpeg_location)


class YtVideoDownloadRequestBody(BaseModel):
    url: str


def generate_random_file_name():
    timestamp_ms = int(time.time() * 1000)
    random_number = random.random()
    return f"{timestamp_ms}{random_number}"


app = FastAPI()
@app.get("/api/info")
def get_info(url: str):
    ydl_opts = {
        "quiet": True,
        "noplaylist": True,
        "ignoreerrors": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return {"error": "Failed to extract video info."}

            return {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "formats": info.get("formats")
            }
        except Exception as e:
            return {"error": str(e)}


@app.get("/")
def health():
    return {"success": "true", "message": f'downloader service running on port {port}'}


@app.post("/api/download")
def download_video(body: YtVideoDownloadRequestBody):
    file_name = f'{generate_random_file_name()}.m4a'
    urls = [body.url]
    ydl_opts = {
        'outtmpl': {
            'default': "/".join([download_path, file_name]),
        },
        'format': 'm4a/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download(urls)

    if error_code == 0:
        return {"status": "success", "file_name": file_name}
    else:
        raise HTTPException(506, detail="download failed for internal server error")
