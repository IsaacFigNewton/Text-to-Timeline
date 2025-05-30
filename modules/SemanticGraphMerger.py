import numpy as np
import networkx as nx
from scipy.optimize import linear_sum_assignment
import re
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
# Importing alignment interface
from modules.Aligner import Aligner
# Importing alignment rules
from modules.GraphAlignmentRule import GraphAlignmentRule,\
                                        ExactMatchRule,\
                                        NamespaceAwareRule,\
                                        FuzzyStringRule,\
                                        StructuralSimilarityRule,\
                                        SubgraphMatchingRule,\
                                        EmbeddingBasedRule

class SemanticGraphMerger(Aligner):
    """
    Enhanced SemanticGraphMerger using a rule-based architecture for progressive alignment.
    """
    
    
    def __init__(self,
                 normalization_model: Callable[[str], str],
                 G0: nx.Graph,
                 G1: nx.Graph,
                 alignment_rules: Optional[List[GraphAlignmentRule]] = None,
                 use_embeddings: bool = False,
                 embedding_model = None):
        """
        Initialize the GraphMerger with progressive alignment capabilities.
        
        Args:
            normalization_model: A function to normalize node labels.
            G0: A SpaCy event subgraph as a NetworkX graph.
            G1: A FRED graph as a NetworkX graph.
            alignment_rules: List of GraphAlignmentRule instances (optional).
            use_embeddings: Whether to use embedding-based similarity.
            embedding_model: Embedding model (only used if use_embeddings=True).
        """
        
        # Validation
        if not callable(normalization_model):
            raise ValueError("normalization_model must be a callable function")
        
        self.normalization_model = normalization_model
        self.use_embeddings = use_embeddings
        self.embedding_model = embedding_model
        
        if use_embeddings and embedding_model is None:
            raise ValueError("embedding_model required when use_embeddings=True")
        
        # Store original graphs for label restoration
        self.G0_original = G0.copy()
        self.G1_original = G1.copy()
        
        # Create normalization mappings
        self.G0_norm_map = {n: normalization_model(n) for n in G0.nodes()}
        self.G1_norm_map = {n: normalization_model(n) for n in G1.nodes()}
        
        # Create reverse mappings for label restoration
        self.G0_reverse_map = {v: k for k, v in self.G0_norm_map.items()}
        self.G1_reverse_map = {v: k for k, v in self.G1_norm_map.items()}
        
        # Apply normalization
        self.G0 = nx.relabel_nodes(G0, self.G0_norm_map)
        self.G1 = nx.relabel_nodes(G1, self.G1_norm_map)
        
        self.G0_node_list = list(self.G0.nodes())
        self.G1_node_list = list(self.G1.nodes())
        
        # Progressive alignment state
        self.entity_map = dict()
        self.alignment_history = []
        
        # Initialize rule-based matchers
        self._initialize_matchers()
        
        # Set up alignment rules
        if alignment_rules is None:
            self.alignment_rules = self._get_default_rules()
        else:
            self.alignment_rules = sorted(alignment_rules, key=lambda x: x.priority)
    

    def _get_default_rules(self) -> List[GraphAlignmentRule]:
        """Get the default set of alignment rules."""
        rules = [
            ExactMatchRule(),
            NamespaceAwareRule(),
            # FuzzyStringRule(threshold=0.8),
            # StructuralSimilarityRule(threshold=0.6),
            SubgraphMatchingRule(threshold=0.5)
        ]
        
        # Add embedding-based rule if embeddings are enabled
        if self.use_embeddings and self.embedding_model:
            rules.append(EmbeddingBasedRule(self.embedding_model, threshold=0.5))
        
        return sorted(rules, key=lambda x: x.priority)
    

    def add_rule(self,
                 rule: GraphAlignmentRule):
        """Add a custom alignment rule."""
        self.alignment_rules.append(rule)
        self.alignment_rules.sort(key=lambda x: x.priority)
    

    def remove_rule(self,
                    rule_name: str):
        """Remove an alignment rule by name."""
        self.alignment_rules = [r for r in self.alignment_rules if r.name != rule_name]
    

    def _initialize_matchers(self):
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


    def progressive_align(self) -> Dict[str, str]:
        """
        Main progressive alignment method using the rule-based architecture.
        Returns: Dictionary mapping G0 nodes to G1 nodes.
        """
        remaining_g0_nodes = set(self.G0_node_list)
        remaining_g1_nodes = set(self.G1_node_list)
        final_entity_map = {}
        
        print(f"Starting progressive alignment with {len(remaining_g0_nodes)} G0 nodes and {len(remaining_g1_nodes)} G1 nodes")
        
        # Apply rules in order of priority
        for rule in self.alignment_rules:
            if not remaining_g0_nodes or not remaining_g1_nodes:
                break
                
            print(f"\nApplying rule: {rule.name}")
            
            matches = rule.find_matches(remaining_g0_nodes, remaining_g1_nodes, self)
            
            # Resolve conflicts using Hungarian algorithm if needed
            if len(matches) > 1:
                matches = self._resolve_conflicts(matches)
            
            # Apply matches
            for g0_node, g1_node, confidence in matches:
                if g0_node in remaining_g0_nodes and g1_node in remaining_g1_nodes:
                    final_entity_map[g0_node] = g1_node
                    remaining_g0_nodes.remove(g0_node)
                    remaining_g1_nodes.remove(g1_node)
                    
                    rule.match_count += 1
                    print(f"  Matched: {g0_node} -> {g1_node} (confidence: {confidence:.3f})")
                    
                    # Store alignment history
                    self.alignment_history.append({
                        'rule': rule.name,
                        'g0_node': g0_node,
                        'g1_node': g1_node,
                        'confidence': confidence
                    })
        
        print(f"\nFinal alignment: {len(final_entity_map)} pairs matched")
        print(f"Remaining unmatched G0 nodes: {len(remaining_g0_nodes)}")
        print(f"Remaining unmatched G1 nodes: {len(remaining_g1_nodes)}")
        
        self.entity_map = final_entity_map
        return final_entity_map


    def _resolve_conflicts(self,
                           matches: List[Tuple[str, str, float]]) -> List[Tuple[str, str, float]]:
        """Resolve conflicts using Hungarian algorithm for optimal assignment."""
        if len(matches) <= 1:
            return matches
        
        # Create sets of unique nodes
        g0_nodes = list(set(match[0] for match in matches))
        g1_nodes = list(set(match[1] for match in matches))
        
        # Create cost matrix (1 - similarity for minimization)
        cost_matrix = np.ones((len(g0_nodes), len(g1_nodes)))
        
        for g0_node, g1_node, confidence in matches:
            i = g0_nodes.index(g0_node)
            j = g1_nodes.index(g1_node)
            cost_matrix[i, j] = 1.0 - confidence
        
        # Apply Hungarian algorithm
        row_indices, col_indices = linear_sum_assignment(cost_matrix)
        
        # Extract optimal matches
        optimal_matches = []
        for i, j in zip(row_indices, col_indices):
            confidence = 1.0 - cost_matrix[i, j]
            if confidence > 0:  # Only include positive similarities
                optimal_matches.append((g0_nodes[i], g1_nodes[j], confidence))
        
        return optimal_matches


    def merge_graphs(self) -> nx.Graph:
        """
        Merge the two graphs based on the current entity mapping.
        Returns: Merged graph with original labels restored.
        """
        if not self.entity_map:
            print("No entity mapping found. Running progressive alignment first.")
            self.progressive_align()
        
        # Create merged graph starting with G0
        merged_graph = self.G0.copy()
        
        # Apply entity mappings to G0
        merged_graph = nx.relabel_nodes(merged_graph, self.entity_map)
        
        # Add G1 edges, merging with existing aligned nodes
        for u, v, data in self.G1.edges(data=True):
            # Check if these nodes are aligned
            u_mapped = u if u not in self.entity_map.values() else u
            v_mapped = v if v not in self.entity_map.values() else v
            
            # Add edge if it doesn't exist or if it adds new information
            if not merged_graph.has_edge(u_mapped, v_mapped):
                merged_graph.add_edge(u_mapped, v_mapped, **data)
            else:
                # Merge edge attributes if needed
                existing_data = merged_graph[u_mapped][v_mapped]
                for key, value in data.items():
                    if key not in existing_data:
                        existing_data[key] = value
        
        # Add unmatched G1 nodes
        for node in self.G1.nodes():
            if node not in self.entity_map.values() and node not in merged_graph.nodes():
                merged_graph.add_node(node, **self.G1.nodes[node])
        
        # Restore original labels
        original_label_map = {}
        for node in merged_graph.nodes():
            if node in self.G0_reverse_map:
                original_label_map[node] = self.G0_reverse_map[node]
            elif node in self.G1_reverse_map:
                original_label_map[node] = self.G1_reverse_map[node]
                
        return nx.relabel_nodes(merged_graph, original_label_map)


    def get_alignment_report(self) -> Dict[str, Any]:
        """Get detailed report of the alignment process."""
        return {
            'total_matches': len(self.entity_map),
            'alignment_history': self.alignment_history,
            'rule_statistics': self._get_rule_statistics(),
            'rule_performance': self._get_rule_performance(),
            'entity_map': self.entity_map
        }
    

    def _get_rule_statistics(self) -> Dict[str, int]:
        """Get statistics about which rules contributed most matches."""
        rule_stats = {}
        for entry in self.alignment_history:
            rule = entry['rule']
            rule_stats[rule] = rule_stats.get(rule, 0) + 1
        return rule_stats
    

    def _get_rule_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for each rule."""
        performance = {}
        for rule in self.alignment_rules:
            performance[rule.name] = {
                'matches_found': rule.match_count,
                'threshold': rule.threshold,
                'confidence_multiplier': rule.confidence_multiplier,
                'priority': rule.priority
            }
        return performance


    # Legacy method for backward compatibility
    def get_map(self) -> Dict[str, str]:
        """Legacy method - calls progressive_align for backward compatibility."""
        return self.progressive_align()