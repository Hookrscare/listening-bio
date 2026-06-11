from fastapi import FastAPI

from backend.app.api.routes import router

app = FastAPI(title="AI Biodiversity Backend", version="0.1.0")
app.include_router(router)

