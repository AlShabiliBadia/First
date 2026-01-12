"""Abstract base class for notification platforms."""

from abc import ABC, abstractmethod
from typing import Dict


class BaseNotifier(ABC):
    """Abstract base class for notification services."""
    
    @abstractmethod
    async def format_message(self, category: str, data: Dict[str, str]) -> dict:
        """
        Format job data for the specific platform.
        
        Args:
            category: The job category.
            data: The job data dictionary.
            
        Returns:
            Formatted message dictionary for the platform.
        """
        pass
    
    @abstractmethod
    async def send(self, target: str, message: dict) -> bool:
        """
        Send a notification to the target.
        
        Args:
            target: The target address (webhook URL, chat ID, etc.).
            message: The formatted message to send.
            
        Returns:
            True if successful, False otherwise.
        """
        pass
