from pathlib import Path
import sqlite3
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "tasks.db"
app = FastAPI(title="Task Manager API", version="2.1.0")

@contextmanager
def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def init_db():
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, description TEXT DEFAULT '',
            due_date TEXT DEFAULT '', priority TEXT NOT NULL DEFAULT 'Medium',
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        cols = {r["name"] for r in db.execute("PRAGMA table_info(tasks)")}
        if "due_date" not in cols:
            db.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT DEFAULT ''")
        if "priority" not in cols:
            db.execute("ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'Medium'")
init_db()

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    due_date: str = Field(default="", max_length=10)
    priority: str = "Medium"

class TaskUpdate(TaskCreate):
    completed: bool = False

class TaskStatus(BaseModel):
    completed: bool

def validate(task):
    if task.priority not in {"Low", "Medium", "High"}:
        raise HTTPException(400, "Priority must be Low, Medium, or High")
    if not task.title.strip():
        raise HTTPException(400, "Task title cannot be empty")

def serialize(row):
    return {"id": row["id"], "title": row["title"], "description": row["description"],
            "due_date": row["due_date"] or "", "priority": row["priority"] or "Medium",
            "completed": bool(row["completed"]), "created_at": row["created_at"]}

@app.get("/api/tasks")
def list_tasks(status: str = "all"):
    if status not in {"all", "pending", "completed"}:
        raise HTTPException(400, "Status must be all, pending, or completed")
    sql = "SELECT * FROM tasks"
    if status == "pending": sql += " WHERE completed=0"
    if status == "completed": sql += " WHERE completed=1"
    sql += " ORDER BY id DESC"
    with get_db() as db:
        return [serialize(r) for r in db.execute(sql).fetchall()]

@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    validate(task)
    with get_db() as db:
        cur = db.execute("INSERT INTO tasks(title,description,due_date,priority) VALUES(?,?,?,?)",
                         (task.title.strip(), task.description.strip(), task.due_date, task.priority))
        return serialize(db.execute("SELECT * FROM tasks WHERE id=?", (cur.lastrowid,)).fetchone())

@app.get("/api/tasks/{task_id}")
def get_task(task_id: int):
    with get_db() as db:
        row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if row is None: raise HTTPException(404, "Task not found")
    return serialize(row)

@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    validate(task)
    with get_db() as db:
        cur = db.execute("""UPDATE tasks SET title=?,description=?,due_date=?,priority=?,completed=?
                            WHERE id=?""",
                         (task.title.strip(), task.description.strip(), task.due_date,
                          task.priority, int(task.completed), task_id))
        if not cur.rowcount: raise HTTPException(404, "Task not found")
        return serialize(db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())

@app.patch("/api/tasks/{task_id}/status")
def set_status(task_id: int, status: TaskStatus):
    with get_db() as db:
        cur = db.execute("UPDATE tasks SET completed=? WHERE id=?", (int(status.completed), task_id))
        if not cur.rowcount: raise HTTPException(404, "Task not found")
        return serialize(db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    with get_db() as db:
        cur = db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        if not cur.rowcount: raise HTTPException(404, "Task not found")
    return {"message": "Task deleted successfully"}

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
@app.get("/")
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")
