from sqlalchemy import create_engine, Index
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from .models import Base, ChatSession, ChatQA, ChatQADubious
from .db_config import DB_CFG


class DatabaseManager:
    """数据库管理器，提供连接管理和自动持久化功能"""
    
    def __init__(self):
        # 构建连接字符串
        self.connection_url = (
            f"mysql+pymysql://{DB_CFG['user']}:{DB_CFG['password']}"
            f"@{DB_CFG['host']}:{DB_CFG['port']}/{DB_CFG['database']}"
            f"?charset={DB_CFG['charset']}"
        )
        
        # 创建引擎
        self.engine = create_engine(
            self.connection_url,
            echo=False,  # 设置为True可以看到SQL语句
            pool_recycle=3600,  # 连接池回收时间
            pool_pre_ping=True,  # 连接前测试
        )
        
        # 创建会话工厂
        self.SessionLocal = scoped_session(sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        ))
    
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)
        
        # 创建索引（如果不存在）
        try:
            # 创建常用查询索引
            idx_qa_session = Index('idx_qa_session_id', ChatQA.session_id)
            idx_dubious_qa = Index('idx_dubious_qa_id', ChatQADubious.qa_id)
            
            idx_qa_session.create(bind=self.engine, checkfirst=True)
            idx_dubious_qa.create(bind=self.engine, checkfirst=True)
        except Exception as e:
            print(f"索引创建警告: {e}")
    
    def drop_tables(self):
        """删除所有表"""
        Base.metadata.drop_all(bind=self.engine)
    
    @contextmanager
    def get_session(self):
        """获取数据库会话（上下文管理器）"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_session_instance(self):
        """获取数据库会话实例（需要手动管理）"""
        return self.SessionLocal()


# 全局数据库管理器实例
db_manager = DatabaseManager()