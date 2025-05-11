from clause_simplification import simplify_clause_structure
from triplet_extraction import get_edges
from fastcoref_coref_resolution import resolve_text
from fastcoref_coref_resolution import disambiguate_refs

def get_referent_from_cluster(cluster_members):
  return max(cluster_members, key=len)

def get_inter_cluster_edges(edges:list, clusters:dict) -> list:
  
  # get a list of nodes that have the word "and" in them
  nodes = set()
  for e in edges:
    if e[0] not in nodes\
      and "and" in e[0].split(" "):
      nodes.add(e[0])
    if e[2] not in nodes\
      and "and" in e[0].split(" "):
      nodes.add(e[2])
  
  # for each node, split on " and "
  for node in nodes:
    members = node.split(" and ")
    for m in members:
      for c_key, c_members in clusters.items():
        # if a member is in a given cluster,
        if m in c_members:
          edges.append((
              get_referent_from_cluster(c_members),
              "member of",
              node
          ))
  
  return edges

def ambiguate_text(text:str,
                   nlp_model,
                   fast_coref_model,
                   coref_resolution_model) -> tuple:
  resolved_text = resolve_text(text,
                               coref_resolution_model=coref_resolution_model)
  return disambiguate_refs(
    text=resolved_text,
    nlp_model=nlp_model,
    fast_coref_model=fast_coref_model
  )

def get_text_info_json(text:str,
                       nlp_model,
                       fastcoref_model,
                       coref_resolution_model) -> dict:
  doc_info = dict()

  doc = nlp_model(text)

  # restructure the text to simplify the clause structure
  doc_info["restructured"] = simplify_clause_structure(doc, nlp_model=nlp_model)
  # get clusters, ambiguated text
  cluster_matches, ambiguated_text = ambiguate_text(text,
                                                    nlp_model,
                                                    fastcoref_model,
                                                    coref_resolution_model)
  doc_info["cluster_matches"] = cluster_matches
  doc_info["ambiguated"] = ambiguated_text
  
  doc = nlp_model(ambiguated_text)

  # get an edge list based on the ambiguated elements
  edges = get_edges(doc_info["restructured"])
  doc_info["edges"] = list()
  # resolve references in the edges based on the longest element of the cluster
  for e in edges:

    e_new = e
    if e[0] in cluster_matches:
      cluster = cluster_matches[e_new[0]]
      longest_string = get_referent_from_cluster(cluster)
      e_new = (longest_string, e_new[1], e_new[2])

    if e[2] in cluster_matches:
      cluster = cluster_matches[e_new[2]]
      longest_string = get_referent_from_cluster(cluster)
      e_new = (e_new[0], e_new[1], longest_string)
    
    doc_info["edges"].append(e_new)

  
  # shift edge labels to lower case
  doc_info["edges"] = [
      (
        e[0].lower(),
        e[1].lower(),
        e[2].lower(),
      ) for e in doc_info["edges"]
  ]

  # get the sequence of events in the text
  events = {e for e in doc_info["edges"] if ("INDOBJ_" not in e[0])}
  doc_info["event_seq"] = list()
  for e in events:
    for i, edge in enumerate(doc_info["edges"]):
      if e == edge and e not in doc_info["event_seq"]:
        doc_info["event_seq"].insert(i, e)
  
  # get inter-cluster edges, for groups of entities
  doc_info["edges"] += get_inter_cluster_edges(
      doc_info["edges"],
      cluster_matches
  )
  
  return doc_info