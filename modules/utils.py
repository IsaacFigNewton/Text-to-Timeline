import networkx as nx
import matplotlib.pyplot as plt

def get_subtree_text(token):
  lefts = [get_subtree_text(t) for t in token.lefts]
  rights = [get_subtree_text(t) for t in token.rights]
  tokens_in_subtree = lefts + [token.text] + rights
  return " ".join(tokens_in_subtree)

def plot_graph_from_edge_list(edges:list):
    # Create a directed graph
    G = nx.DiGraph()

    # Add edges with predicate as edge label
    for subj, pred, obj in edges:
        G.add_edge(subj, obj, label=pred)

    # Draw the graph
    pos = nx.spring_layout(G,  k=2,)  # or try nx.kamada_kawai_layout(G)
    nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=2000, font_size=10, arrows=True)

    # Draw edge labels (predicates)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')

    plt.title("Entity Relationship Graph")
    plt.tight_layout()
    plt.show()