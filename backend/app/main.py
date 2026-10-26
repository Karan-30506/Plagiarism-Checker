from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, upload, reports

app = FastAPI(
    title="Plagiarism Engine API",
    description="Dual-Stream C++ Data Structures Plagiarism Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(reports.router)

@app.get("/")
def root():
    return {"status": "online", "engine": "FastAPI + C++ Core"}