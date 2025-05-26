import json
from collections import defaultdict, deque
from intervaltree import IntervalTree
from utils import remove_rel_prefix
from DSU import DSU
from BoundaryNode import BoundaryNode
from Event import Event

# Apply a single rel_pos_tag between a source boundary and a target event
def apply_tag(tag, source, target_event, graph, dsu):
    rel, boundRef = tag

    # get target boundary if boundRef specified
    if rel == 'sameTimeAs':
        # unify source with target boundary
        target = target_event.start if boundRef == 'start' else target_event.end
        dsu.union(source, target)

    elif rel == 'before':
        target = target_event.start if boundRef == 'start' else target_event.end
        graph[source].add(target)

    elif rel == 'after':
        target = target_event.start if boundRef == 'start' else target_event.end
        graph[target].add(source)

    elif rel == 'during':
        # during: target_event.start -> source, and source_end -> target_event.end
        if source.kind == 'start':
            graph[target_event.start].add(source)
            # record containment
            target_event.children.append(source.event)
        else:
            graph[source].add(target_event.end)

    else:
        raise ValueError(f"Unknown relation {rel}")


def get_timeline(event_seq:list,
                 rel_pos_tags:set,
                 temporal_predicates_map:dict,
                 temporal_relations_map:dict,
                 prefix:str) -> (IntervalTree, set):
    # Cast the combined event triples to Event objects
    event_nodes = {e[0]: Event(e[0]) for e in event_seq}
    event_nodes.update({
      e[2]: Event(e[2]) for e in event_seq
      if e[2] not in event_nodes.keys()
    })

    # DSU for boundary unification
    dsu = DSU()
    # graph edges: boundary -> set(boundary)
    graph = defaultdict(set)

    print(json.dumps(event_seq, indent=4))

    # Process instant relations (single-boundary)
    for t1, rel_name, t2 in event_seq:
        e1, e2 = event_nodes[t1], event_nodes[t2]
        # get the cleaned relation name
        cleaned_rel_name = remove_rel_prefix(rel_name, prefix)
        if cleaned_rel_name not in temporal_relations_map:
            cleaned_rel_name = temporal_predicates_map.get(cleaned_rel_name, cleaned_rel_name)
        # map the relation to indices
        i_start, i_end = temporal_relations_map[cleaned_rel_name]
        # start mapping
        if i_start is not None:
            tag = rel_pos_tags[i_start]
            apply_tag(tag, e1.start, e2, graph, dsu)
        # end mapping
        if i_end is not None:
            tag = rel_pos_tags[i_end]
            apply_tag(tag, e1.end, e2, graph, dsu)

    # Ensure each event.start precedes event.end
    for e in event_nodes.values():
        graph[e.start].add(e.end)

    # Add global boundaries
    global_start = BoundaryNode(None, 'start')
    global_end = BoundaryNode(None, 'end')
    for e in event_nodes.values():
        if not any(e.start in graph[src] for src in graph):
            graph[global_start].add(e.start)
        if len(graph[e.end]) == 0:
            graph[e.end].add(global_end)

    # Consolidate DSU: rebuild nodes and edges on representatives
    rep_graph = defaultdict(set)
    for u, targets in graph.items():
        ru = dsu.find(u)
        for v in targets:
            rv = dsu.find(v)
            if ru != rv:
                rep_graph[ru].add(rv)

    # compute indegree
    indegree = defaultdict(int)
    for u, targets in rep_graph.items():
        indegree.setdefault(u, 0)
        for v in targets:
            indegree[v] += 1

    # Topological sort (Kahn)
    q = deque([
        node for node, deg in indegree.items()
        if deg == 0
    ])
    topo = []
    while q:
        u = q.popleft()
        topo.append(u)
        for v in rep_graph[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                q.append(v)

    # Assign times
    time = 0
    for node in topo:
        node.time = time
        time += 1

    # Build pre-order on containment
    roots = [
        e for e in event_nodes.values()\
        if not any(e in parent.children for parent in event_nodes.values())
    ]

    ordered = []
    def preorder(e):
        ordered.append(e)
        for c in e.children:
            preorder(c)

    for r in roots:
        preorder(r)

    # Build the library’s IntervalTree
    tree = IntervalTree()
    for e in ordered:
        # add interval [begin, end) with payload = the Event instance
        tree.addi(e.start.time, e.end.time, e)   # ← use library insertion :contentReference[oaicite:4]{index=4}

    return tree