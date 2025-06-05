from text_to_timeline.utils.utils import *

# A -type_to_split-> B -other_type-> C
# will be propagated such that
# A -other_type-> C
# and B is removed

# propagate entity types to simplify event descriptions
def propagate_types(g):
    # set of RDF entity type nodes
    type_nodes = set()

    for edge in list(g.edges(data=True)):
        if edge[2]["labels"] == '22-rdf-syntax-ns: type':
            # add the type node to the set
            type_nodes.add(edge[1])

            # for each outgoing edge from the type node (B)
            for type_edge in list(g.edges(edge[1], data=True)):
                # add a copy of the edge between the original source node (A)
                #   and the new target node (C)
                g.add_edge(edge[0], type_edge[1], labels=type_edge[2]["labels"])

            # remove the type edge from the graph
            g.remove_edge(edge[0], edge[1])
            # add the type property to the original source node
            nx.set_node_attributes(g, {edge[0]: edge[1]}, "type")

    # prune RDF entity type nodes
    for node in type_nodes:
        g.remove_node(node)


def prune_subgraph_types(g,
                         node_types_to_drop: set,
                         edge_types_to_drop: set):
    # drop nodes of a certain type
    for node in list(g.nodes):
        for keyword in node_types_to_drop:
            if keyword in node:
                g.remove_node(node)

    # prune redundant edges
    for edge in list(g.edges(data=True)):
        if edge[2]["labels"] in edge_types_to_drop:
            g.remove_edge(edge[0], edge[1])

    # prune orphan nodes
    for node in list(g.nodes()):
        if g.degree(node) == 0:
            g.remove_node(node)


def disambiguate_predicate(e, predicate_map:dict):
    for k, v in predicate_map.items():
        if k in e[2]["labels"]:
            print(k)
            return v
    return e[2]["labels"]


def disambiguate_predicates(g, predicate_map:dict, prefix:str):
    cleaned_edges = list()

    for e in g.edges(data=True):
        if "temp_" in e[2]["labels"]:
            print(e)

            cleaned_edges.append((
                e[0],
                e[1],
                {"labels": add_rel_prefix(disambiguate_predicate(e, predicate_map), prefix)}
            ))

    new_g = nx.DiGraph()
    new_g.add_edges_from(cleaned_edges)
    return new_g