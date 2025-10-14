from typing import List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .BaseDAO import BaseDAO
from .models import ChatSession, ChatQA, ChatQADubious
from .database import db_manager


class ChatSessionDAO(BaseDAO):
    """ChatSession数据访问对象"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session
    
    def _get_session(self) -> Session:
        """获取数据库会话"""
        if self.session:
            return self.session
        return db_manager.get_session_instance()
    
    def create(self, entity: ChatSession) -> ChatSession:
        """创建新的对话会话"""
        session = self._get_session()
        managed_session = not self.session  # 标记是否需要管理session
        try:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            
            # 如果是自管理的session，需要在关闭前获取必要的属性
            if managed_session:
                # 触发属性加载，避免detached状态
                _ = entity.id
                _ = entity.created_at
                _ = entity.updated_at
                
            return entity
        except IntegrityError as e:
            session.rollback()
            raise e
        finally:
            if managed_session:
                session.close()
    
    def get_by_id(self, entity_id: int) -> Optional[ChatSession]:
        """根据ID获取对话会话"""
        session = self._get_session()
        try:
            return session.query(ChatSession).filter(ChatSession.id == entity_id).first()
        finally:
            if not self.session:
                session.close()
    
    def get_all(self) -> List[ChatSession]:
        """获取所有对话会话"""
        session = self._get_session()
        try:
            return session.query(ChatSession).all()
        finally:
            if not self.session:
                session.close()
    
    def update(self, entity: ChatSession) -> bool:
        """更新对话会话"""
        session = self._get_session()
        try:
            session.merge(entity)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            if not self.session:
                session.close()
    
    def delete(self, entity_id: int) -> bool:
        """删除对话会话"""
        session = self._get_session()
        try:
            entity = session.query(ChatSession).filter(ChatSession.id == entity_id).first()
            if entity:
                session.delete(entity)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            if not self.session:
                session.close()
    
    def get_unfinished_sessions(self) -> List[ChatSession]:
        """获取所有未完成的会话"""
        session = self._get_session()
        try:
            return session.query(ChatSession).filter(ChatSession.is_finished == False).all()
        finally:
            if not self.session:
                session.close()
    
    def mark_as_finished(self, entity_id: int, draft: Optional[str] = None) -> bool:
        """标记会话为已完成"""
        session = self._get_session()
        try:
            entity = session.query(ChatSession).filter(ChatSession.id == entity_id).first()
            if entity:
                entity.is_finished = True
                if draft is not None:
                    entity.draft = draft
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            if not self.session:
                session.close()


class ChatQADAO(BaseDAO):
    """ChatQA数据访问对象"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session
    
    def _get_session(self) -> Session:
        """获取数据库会话"""
        if self.session:
            return self.session
        return db_manager.get_session_instance()
    
    def create(self, entity: ChatQA) -> ChatQA:
        """创建新的问答记录"""
        session = self._get_session()
        managed_session = not self.session  # 标记是否需要管理session
        try:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            
            # 如果是自管理的session，需要在关闭前获取必要的属性
            if managed_session:
                # 触发属性加载，避免detached状态
                _ = entity.id
                _ = entity.created_at
                _ = entity.updated_at
                
            return entity
        except IntegrityError as e:
            session.rollback()
            raise e
        finally:
            if managed_session:
                session.close()
    
    def get_by_id(self, entity_id: int) -> Optional[ChatQA]:
        """根据ID获取问答记录"""
        session = self._get_session()
        try:
            return session.query(ChatQA).filter(ChatQA.id == entity_id).first()
        finally:
            if not self.session:
                session.close()
    
    def get_all(self) -> List[ChatQA]:
        """获取所有问答记录"""
        session = self._get_session()
        try:
            return session.query(ChatQA).all()
        finally:
            if not self.session:
                session.close()
    
    def update(self, entity: ChatQA) -> bool:
        """更新问答记录"""
        session = self._get_session()
        try:
            session.merge(entity)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            if not self.session:
                session.close()
    
    def delete(self, entity_id: int) -> bool:
        """删除问答记录"""
        session = self._get_session()
        try:
            entity = session.query(ChatQA).filter(ChatQA.id == entity_id).first()
            if entity:
                session.delete(entity)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            if not self.session:
                session.close()
    
    def get_by_session_id(self, session_id: int) -> List[ChatQA]:
        """根据会话ID获取所有问答记录"""
        session = self._get_session()
        try:
            return session.query(ChatQA).filter(ChatQA.session_id == session_id).order_by(ChatQA.created_at).all()
        finally:
            if not self.session:
                session.close()
    
    def get_by_emotion(self, emotion: str) -> List[ChatQA]:
        """根据情绪获取问答记录"""
        session = self._get_session()
        try:
            return session.query(ChatQA).filter(ChatQA.emotion == emotion).all()
        finally:
            if not self.session:
                session.close()
    
    def update_progress(self, entity_id: int, progress: str) -> bool:
        """更新进度"""
        session = self._get_session()
        try:
            entity = session.query(ChatQA).filter(ChatQA.id == entity_id).first()
            if entity:
                entity.progress = progress
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            if not self.session:
                session.close()


class ChatQADubiousDAO(BaseDAO):
    """ChatQADubious数据访问对象"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session
    
    def _get_session(self) -> Session:
        """获取数据库会话"""
        if self.session:
            return self.session
        return db_manager.get_session_instance()
    
    def create(self, entity: ChatQADubious) -> ChatQADubious:
        """创建新的可疑语句记录"""
        session = self._get_session()
        managed_session = not self.session  # 标记是否需要管理session
        try:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            
            # 如果是自管理的session，需要在关闭前获取必要的属性
            if managed_session:
                # 触发属性加载，避免detached状态
                _ = entity.id
                
            return entity
        except IntegrityError as e:
            session.rollback()
            raise e
        finally:
            if managed_session:
                session.close()
    
    def get_by_id(self, entity_id: int) -> Optional[ChatQADubious]:
        """根据ID获取可疑语句记录"""
        session = self._get_session()
        try:
            return session.query(ChatQADubious).filter(ChatQADubious.id == entity_id).first()
        finally:
            if not self.session:
                session.close()
    
    def get_all(self) -> List[ChatQADubious]:
        """获取所有可疑语句记录"""
        session = self._get_session()
        try:
            return session.query(ChatQADubious).all()
        finally:
            if not self.session:
                session.close()
    
    def update(self, entity: ChatQADubious) -> bool:
        """更新可疑语句记录"""
        session = self._get_session()
        try:
            session.merge(entity)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            if not self.session:
                session.close()
    
    def delete(self, entity_id: int) -> bool:
        """删除可疑语句记录"""
        session = self._get_session()
        try:
            entity = session.query(ChatQADubious).filter(ChatQADubious.id == entity_id).first()
            if entity:
                session.delete(entity)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            if not self.session:
                session.close()
    
    def get_by_qa_id(self, qa_id: int) -> List[ChatQADubious]:
        """根据问答ID获取所有可疑语句记录"""
        session = self._get_session()
        try:
            return session.query(ChatQADubious).filter(ChatQADubious.qa_id == qa_id).all()
        finally:
            if not self.session:
                session.close()
    
    def create_batch(self, entities: List[ChatQADubious]) -> List[ChatQADubious]:
        """批量创建可疑语句记录"""
        session = self._get_session()
        managed_session = not self.session  # 标记是否需要管理session
        try:
            session.add_all(entities)
            session.commit()
            for entity in entities:
                session.refresh(entity)
                # 如果是自管理的session，需要在关闭前获取必要的属性
                if managed_session:
                    _ = entity.id
            return entities
        except IntegrityError as e:
            session.rollback()
            raise e
        finally:
            if managed_session:
                session.close()