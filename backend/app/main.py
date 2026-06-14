from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os, mimetypes

# Ensure 3D print file types are served as binary, not text/plain
mimetypes.add_type('application/octet-stream', '.stl')
mimetypes.add_type('application/vnd.ms-package.3dmanufacturing-3dmodel+xml', '.3mf')
mimetypes.add_type('application/octet-stream', '.gcode')
mimetypes.add_type('application/octet-stream', '.bgcode')
mimetypes.add_type('application/octet-stream', '.step')
mimetypes.add_type('application/octet-stream', '.obj')

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
from app.api.auth import router as auth_router
from app.api.tags import router as tags_router
from app.api.collections import router as collections_router
from app.api.credentials import router as credentials_router
from app.api.admin import router as admin_router
app.include_router(auth_router)
app.include_router(models_router)
app.include_router(tags_router)
app.include_router(collections_router)
app.include_router(credentials_router)
app.include_router(admin_router)

@app.get('/api/health')
async def health():
    return {'status': 'ok', 'service': 'overhang'}
