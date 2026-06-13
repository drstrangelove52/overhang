from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base
import enum

class FileType(str, enum.Enum):
    stl = 'stl'
    file_3mf = '3mf'
    image = 'image'
    other = 'other'

class Model(Base):
    __tablename__ = 'models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    source_url = Column(String(2000))
    source_platform = Column(String(100))
    author = Column(String(255))
    author_url = Column(String(2000))
    license = Column(String(255))
    print_settings = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    files = relationship('ModelFile', back_populates='model', cascade='all, delete-orphan')
    model_tags = relationship('ModelTag', back_populates='model', cascade='all, delete-orphan')

class ModelFile(Base):
    __tablename__ = 'model_files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey('models.id'), nullable=False)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger)
    is_primary_preview = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    model = relationship('Model', back_populates='files')

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)

    model_tags = relationship('ModelTag', back_populates='tag')

class ModelTag(Base):
    __tablename__ = 'model_tags'

    model_id = Column(Integer, ForeignKey('models.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)

    model = relationship('Model', back_populates='model_tags')
    tag = relationship('Tag', back_populates='model_tags')
