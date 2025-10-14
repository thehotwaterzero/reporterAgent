from abc import ABC, abstractmethod
from typing import List, Optional, Any

class BaseDAO(ABC):
    """基础DAO接口"""
    
    @abstractmethod
    def create(self, entity: Any) -> Any:
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[Any]:
        pass
    
    @abstractmethod
    def get_all(self) -> List[Any]:
        pass
    
    @abstractmethod
    def update(self, entity: Any) -> bool:
        pass
    
    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        pass