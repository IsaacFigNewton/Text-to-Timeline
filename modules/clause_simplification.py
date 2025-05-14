from utils import get_subtree_text

def simplify_clause_structure(doc, nlp_model):
  roots = list()
  for token in doc:
    if token.dep_ == "ROOT":
      roots.append(token)

  simplified_text = ""
  for root in roots:
    primary_clause = list()
    secondary_clause = list()

    for child in root.rights:
      # if there's an advanced clause that comes before this one, mark it as such
      if child.dep_ == "advcl":
        print(child.text)
        # if the token isn't the head of an advanced clause
        #   and it's not a temporal marker,
        #   add the token's subtree to the primary clause's text
        primary_clause = [get_subtree_text(child_child)\
                            for child_child in child.lefts\
                            if not (
                                (child_child.pos_ == "SCONJ")
                                # and (child_child.lower in time_markers)
                          )]
        primary_clause += [child.text]
        primary_clause += [get_subtree_text(child_child)\
                            for child_child in child.rights]


    # add the text to the left of the root
    secondary_clause += [get_subtree_text(l) for l in root.lefts]
    secondary_clause += [root.text]
    secondary_clause += [get_subtree_text(r) for r in root.rights if r.dep_ != "advcl"]

    # combine the segmented clauses
    simplified_text += " ".join(primary_clause + [", then"] + secondary_clause)

  return nlp_model(simplified_text)