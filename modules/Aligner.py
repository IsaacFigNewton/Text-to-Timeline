import re

from .POSCategories import POSCategories

class Aligner:
    def __init__(self, G0, G1):
        self.G0 = G0
        self.G1 = G1
        self.pos_categories = POSCategories()

    def _normalize_entity_name(self,
                               name: str) -> str:
        """Apply entity normalization patterns."""
        normalized = name.lower().strip()
        
        pattern_map = self.pos_categories.entity_patterns.items()
        # Apply normalization patterns for entity names
        for pattern, replacement in pattern_map:
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized

    def _normalize_predicate(self,
                             predicate: str) -> str:
        """Apply predicate normalization patterns."""
        normalized = predicate.strip()
        
        pattern_map = self.pos_categories.predicate_patterns.items()
        # Apply normalization patterns for predicates
        for pattern, replacement in pattern_map:
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized