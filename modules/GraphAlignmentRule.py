
import numpy as np
from fuzzywuzzy import fuzz
from networkx.algorithms import isomorphism
from typing import List, Set, Tuple
from abc import ABC, abstractmethod
from Aligner import Aligner

class GraphAlignmentRule(ABC):
    """
    Abstract base class for graph alignment rules.
    Each rule defines a specific strategy for matching nodes between two graphs.
    """
    
    def __init__(self, 
                 name: str, 
                 threshold: float, 
                 confidence_multiplier: float = 1.0,
                 priority: int = 1):
        """
        Initialize the alignment rule.
        
        Args:
            name: Human-readable name for the rule
            threshold: Minimum similarity threshold for matches
            confidence_multiplier: Multiplier for confidence scores
            priority: Rule priority (lower numbers = higher priority)
        """
        self.name = name
        self.threshold = threshold
        self.confidence_multiplier = confidence_multiplier
        self.priority = priority
        self.match_count = 0
        
    @abstractmethod
    def find_matches(self, 
                    g0_nodes: Set[str], 
                    g1_nodes: Set[str], 
                    merger_context: Aligner) -> List[Tuple[str, str, float]]:
        """
        Find potential matches between nodes from two graphs.
        
        Args:
            g0_nodes: Set of remaining unmatched nodes from graph G0
            g1_nodes: Set of remaining unmatched nodes from graph G1
            merger_context: Reference to the Aligner for accessing graphs and utilities
            
        Returns:
            List of tuples (g0_node, g1_node, confidence_score)
        """
        pass
    
    def __lt__(self, other):
        """Enable sorting by priority."""
        return self.priority < other.priority

class ExactMatchRule(GraphAlignmentRule):
    """Rule for exact string matches between node labels."""
    
    def __init__(self):
        super().__init__("Exact Match", threshold=1.0, confidence_multiplier=1.0, priority=1)
    
    def find_matches(self, g0_nodes: Set[str], g1_nodes: Set[str], 
                    merger_context: Aligner) -> List[Tuple[str, str, float]]:
        matches = []
        for g0_node in g0_nodes:
            for g1_node in g1_nodes:
                if g0_node == g1_node:
                    matches.append((g0_node, g1_node, 1.0 * self.confidence_multiplier))
        return matches

class NamespaceAwareRule(GraphAlignmentRule):
    """Rule for namespace-aware matching after normalization."""
    
    def __init__(self):
        super().__init__("Namespace Aware", threshold=0.95, confidence_multiplier=0.95, priority=2)
    
    def find_matches(self, g0_nodes: Set[str], g1_nodes: Set[str], 
                    merger_context: Aligner) -> List[Tuple[str, str, float]]:
        matches = []
        for g0_node in g0_nodes:
            g0_normalized = merger_context._normalize_entity_name(g0_node)
            for g1_node in g1_nodes:
                g1_normalized = merger_context._normalize_entity_name(g1_node)
                if g0_normalized == g1_normalized:
                    matches.append((g0_node, g1_node, self.confidence_multiplier))
        return matches

class FuzzyStringRule(GraphAlignmentRule):
    """Rule for fuzzy string matching using multiple strategies."""
    
    def __init__(self, threshold: float = 0.8):
        super().__init__("Fuzzy String", threshold=threshold, confidence_multiplier=1.0, priority=3)
    
    def find_matches(self,
                     g0_nodes: Set[str],
                     g1_nodes: Set[str], 
                    merger_context: Aligner) -> List[Tuple[str, str, float]]:
        matches = []
        for g0_node in g0_nodes:
            best_match = None
            best_score = 0
            
            for g1_node in g1_nodes:
                # Try multiple fuzzy matching strategies
                ratio_score = fuzz.ratio(g0_node.lower(), g1_node.lower()) / 100.0
                partial_score = fuzz.partial_ratio(g0_node.lower(), g1_node.lower()) / 100.0
                token_sort_score = fuzz.token_sort_ratio(g0_node.lower(), g1_node.lower()) / 100.0
                
                # Use the best score
                score = max(
                    ratio_score,
                    partial_score,
                    token_sort_score
                )
                
                if score >= self.threshold and score > best_score:
                    best_score = score
                    best_match = g1_node
                    
            if best_match:
                matches.append((
                    g0_node,
                    best_match,
                    best_score * self.confidence_multiplier
                ))
        return matches

class StructuralSimilarityRule(GraphAlignmentRule):
    """Rule for structural similarity based on degree and neighbor patterns."""
    
    def __init__(self, threshold: float = 0.6):
        super().__init__("Structural Similarity", threshold=threshold, confidence_multiplier=1.0, priority=4)
    
    def find_matches(self, g0_nodes: Set[str], g1_nodes: Set[str], 
                    merger_context: Aligner) -> List[Tuple[str, str, float]]:
        matches = []
        G0, G1 = merger_context.G0, merger_context.G1
        
        for g0_node in g0_nodes:
            best_match = None
            best_score = 0
            
            g0_degree = G0.degree(g0_node)
            g0_in_degree = G0.in_degree(g0_node) if G0.is_directed() else g0_degree
            g0_out_degree = G0.out_degree(g0_node) if G0.is_directed() else g0_degree
            
            # Get edge label patterns
            g0_edge_labels = set()
            for _, _, data in G0.edges(g0_node, data=True):
                g0_edge_labels.add(merger_context._normalize_predicate(data.get('labels', '')))
            if G0.is_directed():
                for _, _, data in G0.in_edges(g0_node, data=True):
                    g0_edge_labels.add(merger_context._normalize_predicate(data.get('labels', '')))
            
            for g1_node in g1_nodes:
                g1_degree = G1.degree(g1_node)
                g1_in_degree = G1.in_degree(g1_node) if G1.is_directed() else g1_degree
                g1_out_degree = G1.out_degree(g1_node) if G1.is_directed() else g1_degree
                
                # Get edge label patterns
                g1_edge_labels = set()
                for _, _, data in G1.edges(g1_node, data=True):
                    g1_edge_labels.add(merger_context._normalize_predicate(data.get('labels', '')))
                if G1.is_directed():
                    for _, _, data in G1.in_edges(g1_node, data=True):
                        g1_edge_labels.add(merger_context._normalize_predicate(data.get('labels', '')))
                
                # Calculate structural similarity
                degree_sim = 1.0 - abs(g0_degree - g1_degree) / max(g0_degree + g1_degree, 1)
                in_degree_sim = 1.0 - abs(g0_in_degree - g1_in_degree) / max(g0_in_degree + g1_in_degree, 1)
                out_degree_sim = 1.0 - abs(g0_out_degree - g1_out_degree) / max(g0_out_degree + g1_out_degree, 1)
                
                # Edge label similarity (Jaccard coefficient)
                if g0_edge_labels or g1_edge_labels:
                    label_sim = len(g0_edge_labels & g1_edge_labels) / len(g0_edge_labels | g1_edge_labels)
                else:
                    label_sim = 1.0
                
                # Combined structural similarity
                score = (degree_sim + in_degree_sim + out_degree_sim + label_sim) / 4.0
                
                if score >= self.threshold and score > best_score:
                    best_score = score
                    best_match = g1_node
                    
            if best_match:
                matches.append((g0_node, best_match, best_score * self.confidence_multiplier))
        return matches

class SubgraphMatchingRule(GraphAlignmentRule):
    """Rule for subgraph isomorphism matching."""
    
    def __init__(self, threshold: float = 0.5):
        super().__init__("Subgraph Matching", threshold=threshold, confidence_multiplier=1.0, priority=5)
    
    def find_matches(self, g0_nodes: Set[str], g1_nodes: Set[str], 
                    merger_context: Aligner) -> List[Tuple[str, str, float]]:
        matches = []
        G0, G1 = merger_context.G0, merger_context.G1
        
        for g0_node in g0_nodes:
            # Extract 1-hop subgraph around g0_node
            g0_neighbors = set(G0.neighbors(g0_node))
            if G0.is_directed():
                g0_neighbors |= set(G0.predecessors(g0_node))
            g0_subgraph = G0.subgraph([g0_node] + list(g0_neighbors))
            
            best_match = None
            best_score = 0
            
            for g1_node in g1_nodes:
                # Extract 1-hop subgraph around g1_node
                g1_neighbors = set(G1.neighbors(g1_node))
                if G1.is_directed():
                    g1_neighbors |= set(G1.predecessors(g1_node))
                g1_subgraph = G1.subgraph([g1_node] + list(g1_neighbors))
                
                # Use NetworkX's subgraph matching
                try:
                    if G0.is_directed() and G1.is_directed():
                        matcher = isomorphism.DiGraphMatcher(
                            g0_subgraph, g1_subgraph,
                            node_match=lambda n1, n2: fuzz.ratio(str(n1), str(n2)) > 80,
                            edge_match=lambda e1, e2: fuzz.ratio(
                                str(e1.get('labels', '')), 
                                str(e2.get('labels', ''))
                            ) > 70
                        )
                    else:
                        matcher = isomorphism.GraphMatcher(
                            g0_subgraph, g1_subgraph,
                            node_match=lambda n1, n2: fuzz.ratio(str(n1), str(n2)) > 80,
                            edge_match=lambda e1, e2: fuzz.ratio(
                                str(e1.get('labels', '')), 
                                str(e2.get('labels', ''))
                            ) > 70
                        )
                    
                    if matcher.subgraph_is_isomorphic():
                        # Calculate similarity based on subgraph size and structure
                        score = min(len(g0_subgraph.nodes), len(g1_subgraph.nodes)) / max(len(g0_subgraph.nodes), len(g1_subgraph.nodes))
                        
                        if score >= self.threshold and score > best_score:
                            best_score = score
                            best_match = g1_node
                            
                except Exception:
                    # Fallback to simple structural comparison
                    continue
                    
            if best_match:
                matches.append((g0_node, best_match, best_score * self.confidence_multiplier))
        return matches

class EmbeddingBasedRule(GraphAlignmentRule):
    """Rule for embedding-based similarity matching."""
    
    def __init__(self, embedding_model, threshold: float = 0.7):
        super().__init__("Embedding Based", threshold=threshold, confidence_multiplier=1.0, priority=6)
        self.embedding_model = embedding_model
    
    def find_matches(self, g0_nodes: Set[str], g1_nodes: Set[str], 
                    merger_context: Aligner) -> List[Tuple[str, str, float]]:
        if not self.embedding_model:
            return []
            
        matches = []
        
        # Get embeddings for all nodes
        g0_embeddings = {node: self.embedding_model.encode(node) for node in g0_nodes}
        g1_embeddings = {node: self.embedding_model.encode(node) for node in g1_nodes}
        
        for g0_node in g0_nodes:
            best_match = None
            best_score = 0
            
            for g1_node in g1_nodes:
                # Calculate cosine similarity
                similarity = np.dot(g0_embeddings[g0_node], g1_embeddings[g1_node]) / (
                    np.linalg.norm(g0_embeddings[g0_node]) * np.linalg.norm(g1_embeddings[g1_node])
                )
                
                if similarity >= self.threshold and similarity > best_score:
                    best_score = similarity
                    best_match = g1_node
                    
            if best_match:
                matches.append((g0_node, best_match, best_score * self.confidence_multiplier))
                
        return matches