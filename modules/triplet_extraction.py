from utils import get_subtree_text
from spacy.symbols import VERB, AUX


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
    if child.dep_ == "nsubj":
      return child
  return None


def get_subj(verb_root):
  """
  Get the subject of a verb root.
  If the verb root is a conjunction, get the subject from the head of the conjunction.
  """
  subj = None
  for token in verb_root.lefts:
    if token.dep_ == "nsubj":
      return token
  # if the subject is not found, check the head of the conjunction
  if not subj and verb_root.dep_ == "conj":
    return get_subj_from_conj(verb_root.head)


def handle_complement_phrases(
    token,
    suffix:int,
    subj=None,
    pred=None,
    obj=None) -> tuple[list, list]:
  edges = list()
  # if it's an adjectival complement phrase
  if token.dep_ == "acomp":
    # check if the complement phrase has an object as one of its children
    dobj_tok, iobj_tok, prep_modifier_tok = get_verb_conj_objs(token)
    obj = get_subtree_text(dobj_tok) if dobj_tok else None
    # if this is an intermediate token, such as an adjective, but no object
    if not obj:
      # combine the children of this node, as well as the old root,
      #   into a predicate phrase
      left_mods = " ".join([t.text for t in token.lefts])
      pred = f"{pred} {left_mods}"
      obj = get_subtree_text(token)
    # add the indirect object node to the list of nodes
    return [obj], edges

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
    edges.append((nested_subj if nested_subj else subj, "subject", ccomp_obj))
    edges.append((nested_obj if nested_obj else obj, "object", ccomp_obj))

    # add the nodes and edges to the associated lists
    return [ccomp_obj] + comp_nodes,\
            edges + comp_edges
  
  return None, None

def get_subj_dobj(
    verb_root,
    suffix:int) -> tuple[list, list]:
  ind_obj_nodes = list()
  edges = list()

  subj_tok = get_subj(verb_root)
  subj = get_subtree_text(subj_tok) if subj_tok else None
  pred = verb_root.text
  obj = None

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
      pred,
      iobj
    ))
    edges.append((
      subj,
      f"{pred} {iobj} because of",
      dobj
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
        subj,
        pred,
        obj
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
  for chunk in doc.noun_chunks:
      head = chunk.root.head

      # if the verb root has not been checked yet
      if head.text not in verb_roots_checked:

        # if the  parent of the noun chunk is a verb or auxiliary verb
        if head.pos in {VERB, AUX}:

            # recurse on the children of the verb root
            comp_nodes, comp_edges = get_subj_dobj(
                head,
                len(ind_obj_nodes)
            )

            # add the nodes and edges to the associated lists
            ind_obj_nodes = ind_obj_nodes + comp_nodes
            edges = edges + comp_edges

            verb_roots_checked.add(head.text)

  return edges