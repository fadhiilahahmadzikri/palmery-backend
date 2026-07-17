from abc import ABC, abstractmethod
from typing import List, Any
import io

class BaseExporter(ABC):
    """
    Abstract Base Class for all report exporters.
    Enforces a strict contract for generating binary streams of reports.
    """
    
    @abstractmethod
    def generate(self, data: List[Any]) -> io.BytesIO:
        """
        Takes a list of data models and returns a BytesIO stream of the generated file.
        """
        pass
