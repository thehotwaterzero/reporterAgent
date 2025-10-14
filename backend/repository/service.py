from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from .models import ChatSession, ChatQA, ChatQADubious
from .dao_impl import ChatSessionDAO, ChatQADAO, ChatQADubiousDAO
from .database import db_manager


class ChatService:
    """聊天服务类，提供高级业务操作和自动持久化"""
    
    def __init__(self):
        self.session_dao = ChatSessionDAO()
        self.qa_dao = ChatQADAO()
        self.dubious_dao = ChatQADubiousDAO()
    
    def create_new_session(self, draft: Optional[str] = None) -> ChatSession:
        """创建新的对话会话"""
        session = ChatSession(
            is_finished=False,
            draft=draft
        )
        return self.session_dao.create(session)
    
    def add_qa_to_session(self, session_id: int, question: Optional[str] = None, 
                         answer: Optional[str] = None, aim: Optional[str] = None, 
                         emotion: Optional[str] = None, progress: Optional[str] = None) -> ChatQA:
        """向会话添加问答记录"""
        qa = ChatQA(
            session_id=session_id,
            question=question,
            answer=answer,
            aim=aim,
            emotion=emotion,
            progress=progress
        )
        return self.qa_dao.create(qa)
    
    def add_dubious_snippets(self, qa_id: int, snippets: List[str]) -> List[ChatQADubious]:
        """批量添加可疑语句"""
        dubious_records = [
            ChatQADubious(qa_id=qa_id, snippet=snippet)
            for snippet in snippets
        ]
        return self.dubious_dao.create_batch(dubious_records)
    
    def complete_qa_interaction(self, session_id: int, question: str, answer: str,
                               aim: Optional[str] = None, emotion: Optional[str] = None,
                               dubious_snippets: Optional[List[str]] = None,
                               progress: Optional[str] = None) -> ChatQA:
        """完成一次完整的问答交互（包含可疑语句）"""
        # 使用事务确保数据一致性
        with db_manager.get_session() as db_session:
            # 使用同一个session的DAO实例
            qa_dao = ChatQADAO(db_session)
            dubious_dao = ChatQADubiousDAO(db_session)
            
            # 创建问答记录
            qa = ChatQA(
                session_id=session_id,
                question=question,
                answer=answer,
                aim=aim,
                emotion=emotion,
                progress=progress
            )
            qa = qa_dao.create(qa)
            
            # 记录qa的id，用于后续返回
            qa_id = qa.id
            
            # 如果有可疑语句，批量创建
            if dubious_snippets:
                dubious_records = [
                    ChatQADubious(qa_id=qa_id, snippet=snippet)
                    for snippet in dubious_snippets
                ]
                dubious_dao.create_batch(dubious_records)
        
        # 在事务外重新获取对象，避免detached状态
        return self.qa_dao.get_by_id(qa_id)
    
    def get_session_with_qas(self, session_id: int) -> dict:
        """获取包含所有问答记录的会话（返回字典格式避免关联关系问题）"""
        chat_session = self.session_dao.get_by_id(session_id)
        if not chat_session:
            return {}
            
        # 手动加载QA列表
        qa_list = self.qa_dao.get_by_session_id(session_id)
        
        # 构建QA数据，包含可疑语句
        qa_data = []
        for qa in qa_list:
            dubious_list = self.dubious_dao.get_by_qa_id(qa.id)
            qa_data.append({
                "id": qa.id,
                "question": qa.question,
                "answer": qa.answer,
                "aim": qa.aim,
                "emotion": qa.emotion,
                "progress": qa.progress,
                "created_at": qa.created_at,
                "updated_at": qa.updated_at,
                "dubious_records": [
                    {
                        "id": dubious.id,
                        "snippet": dubious.snippet
                    } for dubious in dubious_list
                ]
            })
        
        return {
            "id": chat_session.id,
            "created_at": chat_session.created_at,
            "updated_at": chat_session.updated_at,
            "is_finished": chat_session.is_finished,
            "draft": chat_session.draft,
            "chat_qas": qa_data
        }
    
    def get_qa_with_dubious(self, qa_id: int) -> Optional[ChatQA]:
        """获取包含所有可疑语句的问答记录"""
        with db_manager.get_session() as db_session:
            from sqlalchemy.orm import joinedload
            qa = db_session.query(ChatQA).options(
                joinedload(ChatQA.dubious_records)
            ).filter(ChatQA.id == qa_id).first()
            
            if qa:
                # 触发关联数据的加载
                _ = qa.id
                _ = qa.question
                _ = qa.answer
                _ = qa.emotion
                _ = len(qa.dubious_records)  # 触发dubious_records加载
                
            return qa
    
    def finish_session(self, session_id: int, final_draft: Optional[str] = None) -> bool:
        """结束会话"""
        return self.session_dao.mark_as_finished(session_id, final_draft)
    
    def get_session_statistics(self, session_id: int) -> dict:
        """获取会话统计信息"""
        # 直接使用DAO查询，避免关联关系的复杂性
        chat_session = self.session_dao.get_by_id(session_id)
        if not chat_session:
            return {}
        
        # 单独查询QA记录
        qa_list = self.qa_dao.get_by_session_id(session_id)
        qa_count = len(qa_list)
        
        # 计算可疑语句数量和情绪
        dubious_count = 0
        emotions = []
        for qa in qa_list:
            dubious_list = self.dubious_dao.get_by_qa_id(qa.id)
            dubious_count += len(dubious_list)
            if qa.emotion:
                emotions.append(qa.emotion)
        
        return {
            "session_id": session_id,
            "is_finished": chat_session.is_finished,
            "qa_count": qa_count,
            "dubious_count": dubious_count,
            "emotions": emotions,
            "created_at": chat_session.created_at,
            "updated_at": chat_session.updated_at
        }
    
    def search_by_emotion(self, emotion: str) -> List[ChatQA]:
        """根据情绪搜索问答记录"""
        return self.qa_dao.get_by_emotion(emotion)
    
    def get_recent_sessions(self, limit: int = 10) -> List[ChatSession]:
        """获取最近的会话"""
        with db_manager.get_session() as db_session:
            from sqlalchemy import desc
            sessions = db_session.query(ChatSession).order_by(desc(ChatSession.created_at)).limit(limit).all()
            
            # 触发属性加载，避免detached状态
            for chat_session in sessions:
                _ = chat_session.id
                _ = chat_session.is_finished
                _ = chat_session.created_at
                _ = chat_session.updated_at
                
            return sessions
    
    def get_all_sessions(self) -> Dict[int, ChatSession]:
        """获取所有对话会话
        
        Returns:
            Dict[int, ChatSession]: 字典格式 {session_id: ChatSession对象}
            
        Usage:
            all_sessions = chat_service.get_all_sessions()
            for session_id, session in all_sessions.items():
                print(f"会话 {session_id}: {session.created_at}")
        """
        # 获取所有会话
        sessions = self.session_dao.get_all()
        
        # 转换为字典格式 {session_id: ChatSession}
        result = {}
        for session in sessions:
            result[session.id] = session
            
        return result


# 便捷的服务实例
chat_service = ChatService()