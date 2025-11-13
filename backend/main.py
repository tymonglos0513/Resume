from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import csv
from bs4 import BeautifulSoup
import os
from pydantic import BaseModel
from resume_api import router as resume_router
from log_api import router as log_router
from jobs_api import jobs_router
from dotenv import load_dotenv
import uvicorn
from fastapi.middleware import Middleware
from fastapi.responses import JSONResponse

load_dotenv()

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "defaultkey")
ALLOWED_FRONTEND = os.getenv("ALLOWED_FRONTEND_URL", "http://93.127.142.20:3001/schedules/ammar").rstrip("/")

app = FastAPI(title="Google Sheet Link Extractor")

@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    try:
        key = request.headers.get("X-Auth-Key")
        referer = (request.headers.get("X-Frontend-Source") or "").rstrip("/")

        print(ALLOWED_FRONTEND)
        print(referer)

        # --- 1️⃣ If auth key is correct → allow everything
        if key and key == APP_SECRET_KEY:
            return await call_next(request)

        # --- 2️⃣ Otherwise, allow only from specific frontend URL
        if referer == ALLOWED_FRONTEND:
            return await call_next(request)

        # --- 3️⃣ Otherwise block
        return JSONResponse(
            status_code=403,
            content={"detail": f"Forbidden: Invalid auth key or referer ({referer}, {ALLOWED_FRONTEND})"},
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {str(e)}"},
        )

# Allow frontend access (React dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    	"http://93.127.142.20:3000",
    	"http://93.127.142.20:3000/",
    	"http://93.127.142.20:3001",
    	"http://93.127.142.20:3001/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router)
app.include_router(jobs_router)
app.include_router(log_router)

def fetch_links_from_sheet(sheet_url: str, sheet_name: str):
    """Fetch all links from a public Google Sheet."""
    sheet_id = sheet_url.split("/d/")[1].split("/")[0]
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    response = requests.get(export_url)
    response.raise_for_status()

    decoded = response.content.decode("utf-8").splitlines()
    reader = csv.reader(decoded)

    # Extract only first-column links (normalize)
    links = []
    for row in reader:
        if not row:
            continue
        val = row[0].strip()
        if val.startswith("http"):
            links.append(val)
        else:
            import re
            match = re.search(r"https://[^\s]+", val)
            if match:
                links.append(match.group(0))
    return links

@app.get("/extract")
def extract_links(sheet_url: str = Query(...), sheet_name: str = Query(...)):
    """API endpoint to extract links."""
    try:
        links = fetch_links_from_sheet(sheet_url, sheet_name)
        return {"count": len(links), "links": links}
    except Exception as e:
        return {"error": str(e)}

@app.get("/scrape")
def scrape_url(url: str = Query(...)):
    """Scrape the given URL and return title + meta description + first paragraph."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.title.string.strip() if soup.title else "No title found"
        meta_desc = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            meta_desc = meta["content"].strip()

        first_p = ""
        p = soup.find("p")
        if p:
            first_p = p.get_text(strip=True)

        return {
            "title": title,
            "description": meta_desc or "No meta description found",
            "snippet": first_p or "No paragraph found",
        }
    except Exception as e:
        return {"error": str(e)}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_URL = os.getenv("MODEL_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

class JobPost(BaseModel):
    text: str

@app.post("/analyze_job")
def analyze_job(post: JobPost):
    """Analyze job post text via GitHub Models API and extract structured fields."""
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": MODEL_NAME,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a precise information extraction assistant. "
                        "Your task is to analyze job posts and output a JSON object "
                        "with exactly these fields:\n"
                        "- role_name\n"
                        "- company_name\n"
                        "- work_model (remote / hybrid / onsite)\n"
                        "- hiring_location\n"
                        "Respond ONLY with valid JSON, no explanations."
                    ),
                },
                {"role": "user", "content": post.text},
            ],
        }

        url = MODEL_URL
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()

        print(data)

        content = data["choices"][0]["message"]["content"]
        return {"result": content}

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="certs/localhost-key.pem",
        ssl_certfile="certs/localhost-cert.pem",
    )