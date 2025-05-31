import networkx as nx
import spacy
from nltk.corpus import wordnet as wn
import nltk
from nltk.corpus import framenet as fn
from NodeWSD import NodeWSD

nltk.download('framenet_v17')

class EdgeFD:
    def __init__(self,
                 g,
                 nlp_model=None,
                 wsd_model=None,
                 do_wsd=True):
        """
        Initialize the EdgeFD class with a graph and optional NLP model.
        :param g: The input graph (NetworkX Graph).
        :param nlp_model: Optional spaCy NLP model for processing text.
        :param wsd_model: Optional Word Sense Disambiguation model.
        :param do_wsd: Boolean indicating whether to perform word sense disambiguation.
        """
        self.nlp_model = nlp_model if nlp_model is not None else spacy.load("en_core_web_sm")
        
        if do_wsd:
            # Initialize the Word Sense Disambiguation model and get the disambiguated graph nodes
            self.g = NodeWSD(
                g,
                nlp_model=self.nlp_model,
                wsd_model=wsd_model
            ).g
        else:
            self.g = g
        
        self.framenet = fn

        # Map each node to its FrameNet frame
        self.node_frames = {
            node: self.get_framenet_frame(node) for node in self.g.nodes()
        }

    def get_framenet_frame(self, synset_name: str) -> str:
        """
        Get the FrameNet frame for a given word or synset name.
        :param synset_name: The name of the synset or word to find the frame for.
        :return: The name of the FrameNet frame or None if not found.
        """
        frame = self.framenet.frames_by_lemma([
            lemma.name() for lemma in wn.synset(synset_name).lemmas()
        ])
        return frame[0].name if frame else None