from text_to_timeline.text_rewriting.clause_simplification import simplify_made_it
from text_to_timeline.kg_construction.triplet_extraction import get_edges
from text_to_timeline.kg_construction.fastcoref_coref_resolution import resolve_text, ambiguate_text

def get_referent_from_cluster(cluster_members) -> str:
  return max(cluster_members, key=lambda x: len(x[2]))[2]

def get_inter_cluster_edges(edges:list, clusters:dict) -> list:
  
  # get a list of nodes that have the word "and" in them
  nodes = set()
  for e in edges:
    if e[0] is not None and e[2] is not None:
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


def get_text_info(text:str,
                   nlp_model,
                   fastcoref_model,
                   coref_resolution_model,
                   matcher) -> dict:
  doc_info = dict()
  doc_info["disambiguated"] = resolve_text(
    text,
    coref_resolution_model=coref_resolution_model
  )

  # get clusters and their associated referents, ambiguated text
  cluster_matches, ambiguated_text = ambiguate_text(
    doc_info["disambiguated"],
    fastcoref_model
  )
  doc_info["cluster_matches"] = cluster_matches
  doc_info["ambiguated"] = ambiguated_text
  
  ambiguated_doc = simplify_made_it(
    nlp_model(ambiguated_text),
    matcher)


  # get an edge list based on the ambiguated elements
  edges = get_edges(ambiguated_doc)
  doc_info["edges"] = list()
  # resolve references in the edges based on the longest element of the cluster
  for e in edges:

    e_new = e
    if e_new[0] in cluster_matches:
      cluster = cluster_matches[e_new[0]]
      longest_string = get_referent_from_cluster(cluster)
      e_new = (longest_string, e_new[1], e_new[2])

    if e_new[2] in cluster_matches:
      cluster = cluster_matches[e_new[2]]
      longest_string = get_referent_from_cluster(cluster)
      e_new = (e_new[0], e_new[1], longest_string)
    
    doc_info["edges"].append(e_new)
  
  # shift edge labels to lower case
  doc_info["edges"] = [
      (
        (str(e[0])).lower() if e[0] else None,
        (str(e[1])).lower() if e[1] else None,
        (str(e[2])).lower() if e[2] else None,
      ) for e in doc_info["edges"]
  ]

  # get the sequence of events in the text
  events = {e for e in doc_info["edges"] if (e[0] is not None and ("CCOMP_" not in e[0]))}
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