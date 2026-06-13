from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title='Overhang', version='0.1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

storage_path = os.getenv('STORAGE_PATH', '/app/storage')
os.makedirs(storage_path, exist_ok=True)
app.mount('/api/files', StaticFiles(directory=storage_path), name='files')

from app.api.models import router as models_router
app.include_router(models_router)

@app.get('/api/health')
async def health():
    return {'status': 'ok', 'service': 'overhang'}
