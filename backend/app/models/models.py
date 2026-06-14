from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), unique=True)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    models = relationship('Model', back_populates='user', cascade='all, delete-orphan', passive_deletes=True)
    collections = relationship('Collection', back_populates='user', cascade='all, delete-orphan', passive_deletes=True)


class Model(Base):
    __tablename__ = 'models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    source_url = Column(String(2000))
    source_platform = Column(String(100))
    author = Column(String(255))
    author_url = Column(String(2000))
    license = Column(String(255))
    print_settings = Column(JSON)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship('User', back_populates='models')
    files = relationship('ModelFile', back_populates='model', cascade='all, delete-orphan')
    model_tags = relationship('ModelTag', back_populates='model', cascade='all, delete-orphan')
    collection_models = relationship('CollectionModel', back_populates='model', cascade='all, delete-orphan')


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


class Collection(Base):
    __tablename__ = 'collections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship('User', back_populates='collections')
    collection_models = relationship('CollectionModel', back_populates='collection', cascade='all, delete-orphan')


class PlatformCredential(Base):
    __tablename__ = 'platform_credentials'

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(100), nullable=False, unique=True)
    credential_data = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CollectionModel(Base):
    __tablename__ = 'collection_models'

    collection_id = Column(Integer, ForeignKey('collections.id'), primary_key=True)
    model_id = Column(Integer, ForeignKey('models.id'), primary_key=True)
    position = Column(Integer, default=0)
    added_at = Column(DateTime, server_default=func.now())

    collection = relationship('Collection', back_populates='collection_models')
    model = relationship('Model', back_populates='collection_models')
