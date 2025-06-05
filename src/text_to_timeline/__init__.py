
__version__ = '1.0.1'
__authors__ = 'Isaac Rudnick'
"""
Knowledge Graph Construction and Timeline Analysis Package
A comprehensive toolkit for building knowledge graphs and analyzing temporal relationships.
"""

# Import key classes and functions from each submodule
from .kg_construction.Aligner import *
from .kg_construction.EdgeFD import *
from .kg_construction.GraphAlignmentRule import *
from .kg_construction.NodeWSD import *
from .kg_construction.POSCategories import *
from .kg_construction.SemanticGraphMerger import *

# Import text rewriting functionality
from .text_rewriting.clause_simplification import *

# Import timeline construction classes
from .timeline_construction.BoundaryNode import *
from .timeline_construction.DSU import *
from .timeline_construction.Event import *
from .timeline_construction.timeline_construction import *

# Import utility functions
from .utils.pipeline import *
from .utils.utils import *

# Import processing functions
from .kg_construction.clean_rdf_graph import *
from .kg_construction.fastcoref_coref_resolution import *
from .kg_construction.triplet_extraction import *

__version__ = "0.1.0"
__author__ = "Your Name"

# Optional: define what gets imported with "from package import *"
# You'll need to define this based on what specific functions/classes you want to expose
__all__ = [
    # Add specific function/class names here
    # Example: 'ClassName', 'function_name', etc.
]