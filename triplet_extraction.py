from utils import get_subtree_text
from spacy.symbols import VERB, AUX

def get_prep_obj_from_prep_branch(token, obj_pos_tags:set):
    # get the preposition-object substructure
    for child in token.children:
      if child.dep_ == "prep":
        for child_child in child.children:
          if child_child.dep_ in obj_pos_tags:
            return child.text, child_child.text
    return None, None

def get_subj_from_conj(token):
  for child in token.children:
    if child.dep_ == "nsubj":
      return child.text
  return None

def get_subj_dobj(verb_root, suffix:str):
  ind_obj_nodes = list()
  edges = list()
  obj_pos_tags = {"dobj", "pobj", "iobj"}

  # for each left child of the verb root
  subj = None
  for token in verb_root.lefts:
    # if it's a subject, set the subject as such
    if token.dep_ == "nsubj":
      subj = get_subtree_text(token)
      break

  pred = verb_root.text
  obj = None
  # for each right child of the verb root
  for token in verb_root.rights:
    # if it's a direct object, return
    if token.dep_ in obj_pos_tags:
      obj = get_subtree_text(token)
      break

    # if it's an adjective complement phrase
    elif token.dep_ == "acomp":

      # check if the complement phrase has an object as one of its children
      has_obj = False
      for child in token.children:
        if child.dep_ in obj_pos_tags:
          # if there's no object in the children of this token
          has_obj = True
          # set the object
          obj = get_subtree_text(child)
          break

      # if this is an intermediate token, such as an adjective, but no object
      if not has_obj:
        # combine the children of this node, as well as the old root,
        #   into a predicate phrase
        left_mods = " ".join([t.text for t in token.lefts])
        # right_mods = " ".join([t.text for t in token.rights])
        # pred = f"{verb_root.text} {left_mods} {token.text} {right_mods}"
        # obj = get_prep_obj_from_prep_branch(token, obj_pos_tags)
        pred = f"{verb_root.text} {left_mods}"
        obj = get_subtree_text(token)

      # add the indirect object node to the list of nodes
      ind_obj_nodes.append(obj)
      break

    # if it's a complement phrase
    elif token.dep_ == "ccomp":

      # use a placeholder for the indirect object
      obj = f"INDOBJ_{suffix}"
      edges.append((subj, pred, obj))

      # add the indirect object node to the list of nodes
      ind_obj_nodes.append(obj)

      # recurse on the complement phrase
      comp_nodes, comp_edges = get_subj_dobj(
          token,
          str(len(ind_obj_nodes))
      )

      # the first edge will always be between the local subject and obj/ind-obj
      nested_subj = comp_edges[0][0]
      nested_obj = comp_edges[0][2]

      # add edges to indicate the indirect object's relation to the nested subject and object
      edges.append((obj, "subject", nested_subj))
      edges.append((obj, "object", nested_obj))

      # add the nodes and edges to the associated lists
      ind_obj_nodes = ind_obj_nodes + comp_nodes
      edges = edges + comp_edges
      break

  # if a subject is missing, check to see if this is a conjugate phrase
  if not subj and verb_root.dep_ == "conj":
    # if it is, check the parent phrase for a subject, and use that
    subj = get_subj_from_conj(verb_root.head)

  # if no object was found, then it's probably hidden under a preposition branch
  if not obj:
    prep_addition, obj = get_prep_obj_from_prep_branch(verb_root, obj_pos_tags)
    pred = f"{pred} {prep_addition}" if prep_addition else pred

  edges.append((subj, pred, obj))

  return ind_obj_nodes, edges

def get_edges(doc):
  edges = list()
  ind_obj_nodes = list()
  verb_roots_checked = set()

  # for each noun chunk
  for chunk in doc.noun_chunks:
      head = chunk.root.head

      if head.text not in verb_roots_checked:

        # if the  parent of the noun chunk is a verb
        if head.pos in {VERB, AUX}:

            # recurse on the children of the verb root
            comp_nodes, comp_edges = get_subj_dobj(
                head,
                str(len(ind_obj_nodes))
            )

            # add the nodes and edges to the associated lists
            ind_obj_nodes = ind_obj_nodes + comp_nodes
            edges = edges + comp_edges

            verb_roots_checked.add(head.text)

  return edges