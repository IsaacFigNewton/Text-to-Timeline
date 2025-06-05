"""Data Maps and Configuration Module"""

import json
import os
from pathlib import Path

# Function to load JSON files
def load_json_map(filename):
    """Load a JSON map file from the maps directory"""
    maps_dir = Path(__file__).parent
    filepath = maps_dir / filename
    with open(filepath, 'r') as f:
        return json.load(f)

# Convenience functions for commonly used maps
def load_tags():
    return load_json_map('tags.json')

def load_pronouns():
    return load_json_map('coref_disambiguation/pronouns.json')

def load_allen_intervals():
    return load_json_map('temporal_relations/allen_intervals.json')

def load_predicate_map():
    return load_json_map('temporal_relations/predicate_map.json')