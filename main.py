from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import links,auth_routes
from app.db.database import Base, engine

app = FastAPI()

# create tables automatically
# Base.metadata.create_all(bind=engine)

# ✅ CORS (important for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(links.router, prefix="/links", tags=["links"])

@app.get("/")
def root():
    return {"message": "LinkHub Backend Running 🚀"}