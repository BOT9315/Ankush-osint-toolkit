import os
import csv
import io
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel
from database import init_db, save_result, get_history, get_stats, delete_entry, clear_history
from osint import check_username_async, validate_email, lookup_ip, domain_lookup, image_metadata

app = FastAPI(title="Ankush OSINT Toolkit", version="2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

init_db()


class TargetRequest(BaseModel):
    target: str

@app.get("/api/health")
def health():
    return {"status": "online", "application": "Ankush OSINT Toolkit", "version": "2.1"}


@app.post("/api/username")
async def username_search(request: TargetRequest):
    if not request.target.strip():
        raise HTTPException(400, "Username is required")
    result = await check_username_async(request.target)
    save_result("username", request.target, result)
    return result


@app.post("/api/email")
def email_search(request: TargetRequest):
    if not request.target.strip(): raise HTTPException(400, "Email is required")
    result = validate_email(request.target)
    save_result("email", request.target, result)
    return result


@app.post("/api/ip")
def ip_search(request: TargetRequest):
    if not request.target.strip(): raise HTTPException(400, "IP address is required")
    result = lookup_ip(request.target)
    save_result("ip", request.target, result)
    return result


@app.post("/api/domain")
def domain_search(request: TargetRequest):
    if not request.target.strip(): raise HTTPException(400, "Domain is required")
    result = domain_lookup(request.target)
    save_result("domain", request.target, result)
    return result


@app.post("/api/image")
async def image_search(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    safe_name = os.path.basename(file.filename or "upload")
    file_path = os.path.join("uploads", safe_name)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    result = image_metadata(file_path)
    save_result("image", safe_name, result)
    return result


@app.get("/api/history")
def history(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
            tool: str = Query("all")):
    return get_history(limit=limit, offset=offset, tool=tool)


@app.delete("/api/history/{entry_id}")
def history_delete(entry_id: int):
    if not delete_entry(entry_id):
        raise HTTPException(404, "Entry not found")
    return {"deleted": entry_id}


@app.delete("/api/history")
def history_clear():
    clear_history()
    return {"cleared": True}


@app.get("/api/history/export")
def history_export(format: str = Query("json", pattern="^(json|csv)$")):
    rows = get_history(limit=200, offset=0, tool="all")
    if format == "json":
        return JSONResponse(content=rows)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "tool", "target", "created_at", "result"])
    for row in rows:
        writer.writerow([row["id"], row["tool"], row["target"], row["created_at"], row["result"]])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=investigations.csv"}
    )


@app.get("/api/stats")
def stats():
    return get_stats()


frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=frontend_path), name="assets")


@app.get("/")
def frontend():
    return FileResponse(os.path.join(frontend_path, "index.html"))
