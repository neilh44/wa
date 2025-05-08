from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.config import settings
from app.api import auth, files, whatsapp, storage
from app.utils.security import get_current_user


app = FastAPI(
    title=settings.app_name,
    description="API for WhatsApp to Supabase file upload automation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(files.router, prefix="/api/files", tags=["Files"], dependencies=[Depends(get_current_user)])
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["WhatsApp"], dependencies=[Depends(get_current_user)])
app.include_router(storage.router, prefix="/api/storage", tags=["Storage"], dependencies=[Depends(get_current_user)])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to WhatsApp to Supabase API"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug
    )
