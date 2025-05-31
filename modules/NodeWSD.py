import spacy
import networkx as nx
from nltk.wsd import lesk
from nltk.corpus import wordnet as wn
from POSCategories import POSCategories

class NodeWSD:
    def __init__(self,
                    g,
                    nlp_model=None,
                    wsd_model=None):
        self.nlp_model = nlp_model if nlp_model is not None\
                            else spacy.load("en_core_web_sm")
        self.wsd_model = wsd_model if wsd_model is not None\
                            else lesk
        self.pos_categories = POSCategories()

        # map each noun node in to its disambiguated sense
        self.g = nx.relabel_nodes(
            G=g,
            mapping={
                w: self.synset_to_str(self.node_synset_from_kg(
                    word=w,
                    nlp_model=nlp_model,
                    edge_list=[
                        (e[0], e[2]["labels"], e[1]) for e in g.edges(w, data=True)
                    ]
                )) for w in g.nodes()
            }
        )


    def get_context(self,
                                word:str,
                                edge_list:list) -> str:
        relevant_triple_strings = list()
        # go through all the event's children
        for e in edge_list:
            if word in e[0]\
            or word in e[2]:
                # if the event involves the target entity as the agent
                relevant_triple_strings.append(f"{e[0]} {e[1]} {e[2]}")
        return ". ".join(relevant_triple_strings)


    def node_synset_from_kg(self,
                    word:str,
                    nlp_model,
                    edge_list:list=None,
                    context_doc=None) -> str:
        word_doc = self.nlp_model(word)

        # if the thing is more than 1 token, it's probably a noun
        if (not edge_list) and (context_doc):
            pos = None
            context_doc = word_doc
        
        elif len(word_doc) > 1:
            # if the word is a multi-token phrase, assume it's a noun
            pos = "n"

        else:
            # handle words with unique ids
            word = word.split("_")[0]

            # if no context doc was provided, create one from the edge list
            if not context_doc:
                context_doc = nlp_model(self.get_context(
                        word,
                        edge_list
                ))
            all_word_pos_tags = list()
            for token in context_doc:
                if token.text == word:
                    all_word_pos_tags.append(token.pos_)

            pos = None
            # use the most common POS tag for the word in the context
            try:
                most_frequent_pos = max(all_word_pos_tags,
                                        key=lambda x: all_word_pos_tags.count(x))
                if most_frequent_pos in self.pos_categories.entity_types:
                    pos = "n"
                elif most_frequent_pos in self.pos_categories.predicate_types:
                    pos = "v"
                elif most_frequent_pos in self.pos_categories.modifier_types:
                    pos = "a"
                else:
                    print(all_word_pos_tags)
                    print(word)
                    print(context_doc.text)
                    raise Exception("Invalid POS tag")

            except Exception as ex:
                pos = None
                context_doc = word_doc

        synset = self.wsd_model(
            context_sentence=context_doc.text,
            ambiguous_word=word,
            pos=pos
        )
        if synset is None:
            synset = self.wsd_model(
                context_sentence=context_doc.text,
                ambiguous_word=word
            )
        
        print(f"Word context: {context_doc.text}")
        print(f"Word sense: {self.synset_to_str(synset)}")
        print()

        return synset if synset else None
    

    def synset_to_str(self, synset) -> str:
        """
        Convert a synset to a string representation.
        :param synset: The synset to convert.
        :return: The string representation of the synset.
        """
        # parse the sense/synset label
        return str(synset).split("(")[-1][:-1]