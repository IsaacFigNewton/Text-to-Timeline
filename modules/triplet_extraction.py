from utils import get_subtree_text
from spacy.symbols import VERB, AUX
import spacy
import networkx as nx
from typing import Optional, List, Tuple, Set
from POSCategories import POSCategories

def get_verb_conj_objs(verb):
    # Sometimes, SpaCy will shit itself and believe that there are multiple direct objects
    #   Usually this is from text ambiguation (ie "E1 bought E0 the book.)
    #   Current bandaid solution is to assume that the dobj that has a PROPN tag is the iobj
    dobjs = list()
    iobjs = list()
    prep_modifier = None

    for child in verb.children:
        # Check for a direct object
        # e.g., "the book" in "She gave the book to her."
        if child.dep_ == "dobj":
          dobjs.append(child)

        # Check for a prepositional indirect object: e.g., "to her" in "She gave the book to her."
        elif child.dep_ == "pobj":
          return child, None, None

        # Check for an indirect object
        elif child.dep_ in {"iobj", "dative"}:
          iobjs.append(child)

        # Check for any nested prepositional indirect objects
        elif child.dep_ == "prep":
          prep_modifier = child
          for grandchild in child.children:
            if grandchild.dep_ == "pobj":
              dobjs.append(grandchild)

    # If there are multiple direct objects, assume the first one is the dobj
    if len(dobjs) == 2 and len(iobjs) == 0:
        # If the first dobj is a proper noun, assume it's the indirect object
        if dobjs[0].tag_ == "PROPN":
            return dobjs[1], dobjs[0], prep_modifier
        else:
            return dobjs[0], dobjs[1], prep_modifier
    return dobjs[0] if len(dobjs) > 0 else None,\
            iobjs[0] if len(iobjs) > 0 else None,\
            prep_modifier


# determine the valency of a verb
def get_valency(dobj, iobj):
  # if there's a direct object and indirect object, the verb is transitive
  if dobj and iobj:
    return 2
  # if there's a direct object, but no indirect object, the verb is transitive
  elif dobj:
    return 1
  # if there's no direct object, the verb is intransitive
  else:
    return 0


def get_subj_from_conj(token):
  for child in token.children:
    if child.dep_ in {"nsubj", "nsubjpass"}:
      return child
  return None


def get_subj(verb_root):
  """
  Get the subject of a verb root.
  If the verb root is a conjunction, get the subject from the head of the conjunction.
  """
  subj = None
  for token in verb_root.lefts:
    if token.dep_ in {"nsubj", "nsubjpass"}:
      return token
  # if the subject is not found, check the head of the conjunction
  if not subj and verb_root.dep_ == "conj":
    return get_subj_from_conj(verb_root.head)


def handle_complement_phrases(
    token,
    suffix:int,
    subj_tok=None,
    pred_tok=None,
    obj_tok=None) -> tuple[list, list]:
  subj = get_subtree_text(subj_tok) if subj_tok else None
  pred = get_subtree_text(pred_tok) if pred_tok else None
  obj = get_subtree_text(obj_tok) if obj_tok else None
  edges = list()


  # if it's an adjectival complement phrase
  if token.dep_ == "acomp":
    # check if the complement phrase has an object as one of its children
    dobj_tok, iobj_tok, prep_modifier_tok = get_verb_conj_objs(token)
    acomp_obj = get_subtree_text(dobj_tok) if dobj_tok else None
    # if this is an intermediate token, such as an adjective, but no object
    if not acomp_obj:
      # combine the children of this node, as well as the old root,
      #   into a predicate phrase
      left_mods = " ".join([t.text for t in token.lefts])
      pred = f"{pred} {left_mods}"
      acomp_obj = get_subtree_text(token)
    # add the indirect object node to the list of nodes
    return [acomp_obj], edges

  # if it's a clausal complement phrase
  elif token.dep_ in {"advcl", "ccomp"}:
    # use a placeholder for the indirect object
    ccomp_obj = f"CCOMP_{suffix}"
    edges.append((subj, pred, ccomp_obj))
    # recurse on the complement phrase
    comp_nodes, comp_edges = get_subj_dobj(
        token,
        suffix+1
    )

    # the first edge will always be between the local subject and obj/ind-obj
    nested_subj = comp_edges[0][0]
    nested_obj = comp_edges[0][2]
    # add edges to indicate the indirect object's relation to the nested subject and object
    if nested_subj:
      edges.append((
        nested_subj,
        "subject",
        ccomp_obj
      ))
    if nested_obj:
      edges.append((
        nested_obj,
        "object",
        ccomp_obj
      ))

    # if the complement phrase is in passive voice,
    #   link the subject of the complement phrase to the predicate using an auxiliary verb
    for child in token.children:
      # ensure the clausal complement phrase has an auxiliary verb modifying it
      #  and no object was found in the complement phrase
      if child.dep_ == "auxpass" and not nested_obj:
        # link the subject and current predicate using the auxiliary verb
        edges.append((
          nested_subj,
          get_subtree_text(child),
          pred
        ))
        break
    
    # if the subject of the complement phrase
    #   is also the subject of the complement phrase's object (which may be a verb phrase)
    #   prune the subject of the complement phrase's object
    # remove the subject from the edges
    comp_edges = [e for e in comp_edges\
                  if not(obj\
                    and (subj in e[0])\
                    and ("subject" in e[1])\
                    and (obj in e[2]))]

    # add the nodes and edges to the associated lists
    return [ccomp_obj] + comp_nodes,\
            edges + comp_edges
  
  
  # if the child is a conjunction, recurse on the conjunction
  elif token.dep_ == "conj":
    comp_nodes, comp_edges = get_subj_dobj(
      child,
      suffix+1,
      subj_tok=subj_tok
    )
    
    # add the nodes and edges to the associated lists
    return [ccomp_obj] + comp_nodes,\
            edges + comp_edges

  return None, None

def get_subj_dobj(
    verb_root,
    suffix:int,
    subj_tok=None,
    obj=None) -> tuple[list, list]:
  ind_obj_nodes = list()
  edges = list()

  if not subj_tok:
    subj_tok = get_subj(verb_root)
  subj = get_subtree_text(subj_tok) if subj_tok else None
  pred = verb_root.text

  # Get the direct object and indirect object, as well as any prepositional modifier
  dobj_tok, iobj_tok, prep_modifier_tok = get_verb_conj_objs(verb_root)
  dobj = get_subtree_text(dobj_tok) if dobj_tok else None
  iobj = get_subtree_text(iobj_tok) if iobj_tok else None

  # get the verb's valency to determine the predicate
  verb_valency = get_valency(dobj, iobj)
  
  # if the verb is ditransitive, i.e., has both a direct and indirect object
  if verb_valency == 2:
    pred = get_subtree_text(
      verb_root,
      exclude=[subj_tok, dobj_tok, iobj_tok, prep_modifier_tok]
    )
    edges.append((
      subj,
      "subject",
      f"DITRANSITIVE_{suffix}"
    ))
    edges.append((
      pred,
      "action",
      f"DITRANSITIVE_{suffix}"
    ))
    edges.append((
      iobj,
      "object",
      f"DITRANSITIVE_{suffix}"
    ))
    edges.append((
      dobj,
      "motivator",
      f"DITRANSITIVE_{suffix}"
    ))
    return ind_obj_nodes, edges

  # if the verb is transitive
  elif verb_valency == 1:
    pred = get_subtree_text(
      verb_root,
      exclude=[subj_tok, dobj_tok, iobj_tok]
    )
    edges.append((subj, pred, dobj))
    return ind_obj_nodes, edges

  # if the verb is intransitive, but has an adjectival or clausal complement
  elif verb_valency == 0:
    # for each right child of the verb root
    for token in verb_root.rights:
      # handle complement phrases
      addtl_iobj_nodes, complement_edges = handle_complement_phrases(
        token,
        suffix,
        subj_tok=subj_tok,
        pred_tok=verb_root
      )
      if addtl_iobj_nodes is not None and complement_edges is not None:
        return ind_obj_nodes + addtl_iobj_nodes,\
                edges + complement_edges

    # if the verb root has no objects or complements,
    # the verb is probably intransitive and no additional relations can be extracted,
    #   so use the verb root as the object
    if not dobj:
      obj = get_subtree_text(
        verb_root,
        exclude=[subj_tok]
      )
      edges.append((subj, "subject", obj))
      return ind_obj_nodes, edges
  
  return None, None


def get_edges(doc):
  edges = list()
  ind_obj_nodes = list()
  verb_roots_checked = set()

  # for each noun chunk
  for token in doc:
        # if the  parent of the noun chunk is a verb or auxiliary verb
        if token.dep_ in {"ROOT"}\
          and token.pos_ in {"VERB", "AUX"}:

            # recurse on the children of the verb root
            comp_nodes, comp_edges = get_subj_dobj(
                token,
                len(ind_obj_nodes)
            )

            # add the nodes and edges to the associated lists
            ind_obj_nodes = ind_obj_nodes + comp_nodes
            edges = edges + comp_edges

            verb_roots_checked.add(token.text)

  return edges


class SplitTriplets:

    def __init__(self,
        subj_edge_label:str="subject",
        obj_edge_label:str="object"):
        
        self.subj_edge_label = subj_edge_label
        self.obj_edge_label = obj_edge_label
        self.pos_categories = POSCategories()

    def get_node_subgraph(
        self,
        chunk:str,
        nlp_model,
        event_id:int=None):

      root = None
      id = event_id if event_id else int(str(hash(chunk))[:10])
      chunk_graph = nx.DiGraph()
      doc = nlp_model(chunk)

      # print(f"entities: {doc.ents}")
      entity = doc.ents[0] if len(doc.ents) > 0 else None

      # if an entity was extracted from the noun chunk
      if entity:
        root = entity.text
        root_type = "PROPN"
        chunk_graph.add_edge(
          root,
          entity[0].ent_type_,
          labels="rdf-schema: subClassOf"
        )

      # otherwise, just try extracting a noun
      else:
        for word in doc:
          if word.pos_ in self.pos_categories.entity_types:
            root = word.text
            root_type = "NOUN"
            break

      if root is None:
        # try extracting a verb
        for word in doc:
          if word.pos_ in self.pos_categories.predicate_types\
            or word.pos_ in {"ADV"}:
            root = word.text + "_" + str(id)
            root_type = word.pos_
            break
      if root is None:
        # check if the chunk is an ADJ
        if doc[0].pos_ == "ADJ":
          root = doc[0].text
          root_type = "ADJ"

      # if root is still None
      if root is None:
        print(f"event_id: {id}")
        print(f"chunk: {chunk}")
        print(f"chunk pos: {doc[0].pos_}")
        raise ValueError("No root node found or not implemented.")

      # add other words' dependencies to the graph
      for word in doc:
        if word.text not in root:
          if word.pos_ in self.pos_categories.modifier_types:
            chunk_graph.add_edge(root, word.text, labels="DUL.owl: hasQuality")
          elif word.pos_ in self.pos_categories.locator_types:
            chunk_graph.add_edge(root, word.text, labels="hasSpatiotemporalLocation")
          elif word.pos_ in self.pos_categories.determiner_types:
            chunk_graph.add_edge(root, word.text, labels="quantifiers.owl: hasDeterminer")
          elif word.pos_ in self.pos_categories.quantifier_types:
            chunk_graph.add_edge(root, word.text, labels="quantifiers.owl: hasQuantity")

      return root, chunk_graph, root_type


    def get_triple_subgraph(
        self,
        e,
        nlp_model,
        event_id:int=None):
      node_subgraphs = nx.DiGraph()

      # get subgraph for the subject's noun chunk
      subj, subj_subgraph, subj_type = self.get_node_subgraph(
          e[0],
          nlp_model
      )
      node_subgraphs.update(subj_subgraph)

      # get subgraph for the predicate's verb phrase
      pred, pred_subgraph, pred_type = self.get_node_subgraph(
          e[1],
          nlp_model,
          event_id=event_id
      )
      node_subgraphs.update(pred_subgraph)

      # get subgraph for the object's noun chunk
      obj, obj_subgraph, obj_type = self.get_node_subgraph(
          e[2],
          nlp_model,
      )


      # if the predicate was an AUX and the object type is an adjective
      if pred_type == "AUX" and obj_type == "ADJ":
        node_subgraphs.add_edge(subj, obj, labels="DUL.owl: hasQuality")
      # otherwise, it should be fine to add the object to the graph as an object
      else:
        node_subgraphs.update(obj_subgraph)
        node_subgraphs.add_edge(
          pred,
          obj,
          labels=self.obj_edge_label
        )

      node_subgraphs.add_edge(
        pred,
        subj,
        labels=self.subj_edge_label
      )

      return subj, pred, obj, node_subgraphs


    def split_event_triples(self, event_triples:list, nlp_model):
      event_subgraphs = nx.DiGraph()
      noun_nodes = set()
      new_event_seq = list()

      for i, e in enumerate(event_triples):
        subj, event_root, obj, node_subgraphs = self.get_triple_subgraph(e, nlp_model, i)
        # add the event root (predicate) to the event sequence
        #   since a unique id is appended to each predicate node's label,
        #   there should be no confusion for repeated actions/verbs
        new_event_seq.append(event_root)
        # add the noun nodes to the list
        #   this will be helpful for wsd disambiguation and FRED event association
        noun_nodes.add(subj)
        noun_nodes.add(obj)
        # add the triple's subgraph to the larger graph
        event_subgraphs.update(node_subgraphs)

      # add temporal relations implied by the event_seq
      for i in range(len(new_event_seq)-1):
        event_subgraphs.add_edge(
          new_event_seq[i],
          new_event_seq[i+1],
          labels="boxer.owl: temp_before"
        )

      return event_subgraphs, new_event_seq, noun_nodes

    def __repr__(self):
        return f"({self.subj}, {self.pred}, {self.obj})"

    def __eq__(self, other):
        return (self.subj == other.subj and
                self.pred == other.pred and
                self.obj == other.obj)