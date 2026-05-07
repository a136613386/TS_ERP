"""
知识库模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class KnowledgeBase(Base):
    """知识库模型"""
    __tablename__ = "knowledge_bases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    module = Column(String(50), default="general")
    is_active = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    documents = relationship("Document", back_populates="base")
    creator = relationship("User")


class Document(Base):
    """文档模型"""
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    base_id = Column(Integer, ForeignKey('knowledge_bases.id'), nullable=False)
    title = Column(String(200), nullable=False)
    file_path = Column(String(500))
    file_type = Column(String(50))
    file_hash = Column(String(64))
    file_size = Column(Integer)
    status = Column(String(20), default="pending")  # pending/processing/completed/failed
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    indexed_at = Column(DateTime)
    
    # 关系
    base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document")
    uploader = relationship("User")


class Chunk(Base):
    """知识块模型"""
    __tablename__ = "knowledge_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('knowledge_documents.id'), nullable=False)
    chunk_index = Column(Integer)
    content = Column(Text)
    summary = Column(String(500))
    es_doc_id = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    document = relationship("Document", back_populates="chunks")
