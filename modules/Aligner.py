from abc import ABC, abstractmethod
import re
from typing import Dict, List, Tuple

class Aligner:
    def __init__(self, G0, G1):
        self.G0 = G0
        self.G1 = G1

    def _normalize_entity_name(self,
                               name: str) -> str:
        """Apply entity normalization patterns."""
        normalized = name.lower().strip()
        
        for pattern, replacement in self.entity_patterns.items():
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized

    def _normalize_predicate(self,
                             predicate: str) -> str:
        """Apply predicate normalization patterns."""
        normalized = predicate.strip()
        
        for pattern, replacement in self.predicate_patterns.items():
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized