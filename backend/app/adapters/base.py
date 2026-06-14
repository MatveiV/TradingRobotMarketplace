from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class TradingAdapter(ABC):
    @abstractmethod
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        pass
    
    @abstractmethod
    async def get_trade_history(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict]:
        pass
    
    @abstractmethod
    async def get_performance(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        pass