# ---- Jobs save/load endpoints ----
from fastapi import Body, APIRouter, Query
import os, json
from datetime import datetime
import time

jobs_router = APIRouter(prefix="/jobs", tags=["Jobs"])

INDEX_PATH = os.path.join("data", "jobs", "index.json")

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def _read_index() -> dict:
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def _write_index(data: dict):
    _ensure_dir(os.path.dirname(INDEX_PATH))
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@jobs_router.post("/save")
def save_job_description(payload: dict = Body(...)):
    """
    Save a job description for a given sheet name and link number.
    Body: { "url": str, "number": int, "sheet_name": str, "text": str }
    """
    url = payload.get("url", "").strip()
    number = str(payload.get("number", "")).strip()
    sheet_name = payload.get("sheet_name", "").strip()
    text = payload.get("text", "")

    if not url or not number or not sheet_name or not text.strip():
        return {"error": "Missing url, number, sheet_name, or text"}

    base_dir = os.path.join("data", "jobs", sheet_name, number)
    _ensure_dir(base_dir)

    file_path = os.path.join(base_dir, "job_description.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

    # Update index
    index = _read_index()
    index[url] = {"sheet_name": sheet_name, "number": number}
    _write_index(index)

    return {"success": True, "path": file_path, "sheet_name": sheet_name, "number": number}

@jobs_router.get("/load")
def load_job_description(url: str):
    """
    Load a previously saved job description by URL.
    Returns { found: bool, text?: str, sheet_name?: str, number?: str }
    """
    index = _read_index()
    entry = index.get(url)
    if not entry:
        return {"found": False}

    sheet_name, number = entry.get("sheet_name"), entry.get("number")
    file_path = os.path.join("data", "jobs", sheet_name, number, "job_description.txt")
    if not os.path.exists(file_path):
        return {"found": False}

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    return {"found": True, "text": text, "sheet_name": sheet_name, "number": number}

@jobs_router.post("/generate_custom_resumes")
def generate_all_custom_resumes(payload: dict = Body(...)):
    """
    Generate customized resumes for all job links that have job_description.txt
    Body: { "sheet_name": str, "resume": dict }
    """

    from pathlib import Path
    sheet_name = payload.get("sheet_name")
    base_resume = payload.get("resume")

    if not sheet_name or not base_resume:
        return {"error": "Missing sheet_name or resume"}

    jobs_dir = Path("data") / "jobs" / sheet_name
    if not jobs_dir.exists():
        return {"error": f"No jobs found for sheet '{sheet_name}'"}

    all_numbers = sorted(
        [p.name for p in jobs_dir.iterdir() if p.is_dir()],
        key=lambda x: int(x)
    )

    total = len(all_numbers)
    done = 0
    generated = []

    for number in all_numbers:
        desc_path = jobs_dir / number / "job_description.txt"
        if not desc_path.exists():
            continue

        text = desc_path.read_text(encoding="utf-8").strip()
        if not text:
            continue

        try:
            # call /resume/customize internally
            import requests
            r = requests.post(
                "http://93.127.142.20:8000/resume/customize",
                json={"resume": base_resume, "job_description": text},
                timeout=180,
            )
            r.raise_for_status()
            custom_resume = r.json()
            _ensure_dir(jobs_dir / number / base_resume.get("name"))
            (jobs_dir / number / base_resume.get("name") / "custom_resume.json").write_text(
                json.dumps(custom_resume, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            generated.append(number)
        except Exception as e:
            print(f"❌ Failed job #{number}: {e}")
            continue

        done += 1
        time.sleep(0.2)  # small delay to reduce model rate limit load

    return {
        "success": True,
        "sheet_name": sheet_name,
        "generated_count": len(generated),
        "total": total,
        "generated_numbers": generated,
    }

@jobs_router.get("/file/exists")
def file_exists(path: str = Query(...)):
    import os
    return {"exists": os.path.exists(path)}

@jobs_router.get("/file/read_json")
def file_read_json(path: str = Query(...)):
    import os, json
    if not os.path.exists(path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data