# TaskNest Task Manager

A redesigned, simple task manager with a layout different from the supplied Daymark screenshots.

## Technology
- Frontend: HTML, CSS, JavaScript
- Backend: Python FastAPI
- Database: SQLite

## Run on Windows
Open this folder in VS Code and run these commands in the terminal:

```powershell
py -m pip install -r requirements.txt
py -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

## Features
- Add, edit and delete tasks
- Mark tasks complete or pending
- All, Pending and Completed filters
- Search tasks
- Due date and priority
- Dashboard counts and progress
- Responsive design

## API routes
- GET /api/tasks?status=all|pending|completed
- GET /api/tasks/{id}
- POST /api/tasks
- PUT /api/tasks/{id}
- PATCH /api/tasks/{id}/status
- DELETE /api/tasks/{id}

No login/authentication is included in this version.
