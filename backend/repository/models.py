from sqlalchemy import Column, BigInteger, DateTime, Text, VARCHAR, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
from typing import List

Base = declarative_base()


class ChatSession(Base):
    """对话窗口主表"""
    __tablename__ = 'chat_session'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, default=func.current_timestamp(), 
                       onupdate=func.current_timestamp())
    is_finished = Column(Boolean, nullable=False, default=False)
    draft = Column(Text, nullable=True)
    
    # 关联关系
    chat_qas = relationship("ChatQA", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, created_at={self.created_at}, is_finished={self.is_finished})>"


class ChatQA(Base):
    """问答表"""
    __tablename__ = 'chat_qa'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey('chat_session.id', ondelete='CASCADE'), nullable=False)
    question = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    aim = Column(VARCHAR(255), nullable=True)
    emotion = Column(VARCHAR(50), nullable=True)
    progress = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    updated_at = Column(DateTime, nullable=False, default=func.current_timestamp(), 
                       onupdate=func.current_timestamp())
    
    # 关联关系
    session = relationship("ChatSession", back_populates="chat_qas")
    dubious_records = relationship("ChatQADubious", back_populates="qa", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatQA(id={self.id}, session_id={self.session_id}, aim={self.aim}, emotion={self.emotion})>"


class ChatQADubious(Base):
    """可疑语句子表"""
    __tablename__ = 'chat_qa_dubious'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    qa_id = Column(BigInteger, ForeignKey('chat_qa.id', ondelete='CASCADE'), nullable=False)
    snippet = Column(Text, nullable=False)
    
    # 关联关系
    qa = relationship("ChatQA", back_populates="dubious_records")
    
    def __repr__(self):
        return f"<ChatQADubious(id={self.id}, qa_id={self.qa_id}, snippet={self.snippet[:50]}...)>"