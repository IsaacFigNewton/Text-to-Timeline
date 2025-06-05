import networkx as nx
import matplotlib.pyplot as plt
from intervaltree import IntervalTree

from .Event import Event


def get_subtree_text(token, exclude=list()):
  dep_types_to_exclude = [
      "punct", "mark"
  ]
  lefts = [get_subtree_text(t) for t in token.lefts\
           if (t not in exclude)\
            and (t.dep_ not in dep_types_to_exclude)]
  rights = [get_subtree_text(t) for t in token.rights\
           if (t not in exclude)\
            and (t.dep_ not in dep_types_to_exclude)]
  tokens_in_subtree = lefts + [token.text] + rights
  return " ".join(tokens_in_subtree)


def plot_graph_from_edge_list(
    edges:list,
    k=2,
    shape=(20, 20)
    ):
    # Create a directed graph
    G = nx.DiGraph()

    # Add edges with predicate as edge label
    for subj, pred, obj in edges:
      G.add_edge(
        str(subj),
        str(obj),
        label=pred
      )

    # Draw the graph
    pos = nx.spring_layout(
      G,
      k=k,
    )
    plt.figure(figsize=shape, dpi=100)
    nx.draw(
      G,
      pos,
      with_labels=True,
      node_color="lightblue",
      node_size=2000,
      font_size=10,
      arrows=True
    )

    # Draw edge labels (predicates)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(
      G,
      pos,
      edge_labels=edge_labels,
      font_color='red'
    )

    plt.title("Entity Relationship Graph")
    # plt.tight_layout()
    plt.show()


def murder_orphans(g):
  # prune orphan nodes
  for node in list(g.nodes()):
    if g.degree(node) == 0:
      g.remove_node(node)


def complete_rel_from_partial_match(label:str, relations:set, prefix):
  for k in relations:
    if k in label:
      return add_rel_prefix(k, prefix)
  return label


def add_rel_prefix(rel:str, prefix:str):
  if prefix not in rel:
    return f"{prefix}{rel}"
  return rel


def remove_rel_prefix(rel:str, prefix:str):
  return rel.replace(prefix, "")


def list_nodes(g, drop_prefix:bool=False):
  if drop_prefix:
    return [node.split(" ")[-1] for node, _ in list(g.nodes(data=True))]
  else:
    return [node for node, _ in list(g.nodes(data=True))]


def list_triples(g, drop_prefix:bool=False):
  triples = list(g.edges(data=True))

  if drop_prefix:
    triples = [
        (
            subject.split(" ")[-1],
            predicate["labels"].split(" ")[-1],
            object1.split(" ")[-1]
        ) for subject, object1, predicate in triples
    ]

  else:
    triples = [
        (
            subject,
            predicate["labels"],
            object1
        )
        for subject, object1, predicate in triples
    ]

  return triples


def print_interval_tree(tree):
  for interval in tree:
    print(f"Interval: {interval}")
    print(f"  Begin: {interval.begin}")
    print(f"  End: {interval.end}")
    print(f"  Data: {interval.data}")


def plot_interval_tree(tree:IntervalTree, grid:bool=True):
  # Prepare data
  intervals = sorted(tree)
  fig, ax = plt.subplots()

  for i, iv in enumerate(intervals):
    ax.broken_barh(
        [(iv.begin, iv.end - iv.begin)],
         (i - 0.4, 0.8),
        facecolors='tab:blue'
    )
    ax.text(
        (iv.begin + iv.end) / 2,
        i,
        iv.data.id.split(" ")[-1],
        ha='center',
        va='center',
        color='white'
    )

  ax.set_yticks(range(len(intervals)))
  ax.set_yticklabels([f"Interval {i+1}" for i in range(len(intervals))])
  ax.set_xlabel("Timeline")
  ax.set_title("IntervalTree Visualization")

  if grid:
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    # plt.grid(True)

  plt.tight_layout()
  plt.show()