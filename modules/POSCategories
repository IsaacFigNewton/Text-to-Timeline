class POSCategories:
    def __init__(self):
        self.entity_types = {"PROPN", "NOUN", "PRON"}
        self.predicate_types = {"VERB", "AUX"}
        self.modifier_types = {"ADJ", "ADV"}
        self.locator_types = {"ADP", "ADV"}
        self.determiner_types = {"DET"}
        self.quantifier_types = {"NUM", "CARDINAL", "ORDINAL"}
    
        """Initialize rule-based matching components."""
        # Entity name normalization patterns
        self.entity_patterns = {
            r'(.+)_\d+$': r'\1',  # Remove numeric suffixes
            r'domain\.owl:\s*(.+)': r'\1',  # Remove domain.owl prefix
            r'quantifiers\.owl:\s*(.+)': r'\1',  # Remove quantifiers.owl prefix
            r'DUL\.owl:\s*(.+)': r'\1',  # Remove DUL.owl prefix
            r'boxer\.owl:\s*(.+)': r'\1',  # Remove boxer.owl prefix
        }
        
        # Predicate normalization patterns
        self.predicate_patterns = {
            r'quantifiers\.owl:\s*hasDeterminer': 'hasDeterminer',
            r'DUL\.owl:\s*hasQuality': 'hasQuality',
            r'boxer\.owl:\s*temp_before': 'temp_before',
        }