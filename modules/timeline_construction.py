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


# Main function to build timeline
def build_interval_timeline(event_names,
                            temporal_relations_input,
                            rel_pos_tags:list,
                            temporal_relations_map:str,
                            prefix:str):
    # Create events
    events = {name: Event(name) for name in event_names}

    # DSU for boundary unification
    dsu = DSU()
    # graph edges: boundary -> set(boundary)
    graph = defaultdict(set)

    # Helper to add edge post-union normalization
    def add_edge(u, v):
        graph[u].add(v)

    print(json.dumps(temporal_relations_input, indent=4))

    # Process instant relations (single-boundary)
    for t1, rel_name, t2 in temporal_relations_input:
        e1, e2 = events[t1], events[t2]
        i_start, i_end = temporal_relations_map[remove_rel_prefix(rel_name, prefix)]
        # start mapping
        if i_start is not None:
            tag = rel_pos_tags[i_start]
            apply_tag(tag, e1.start, e2, graph, dsu)
        # end mapping
        if i_end is not None:
            tag = rel_pos_tags[i_end]
            apply_tag(tag, e1.end, e2, graph, dsu)

    # Ensure each event.start precedes event.end
    for e in events.values():
        graph[e.start].add(e.end)

    # Add global boundaries
    global_start = BoundaryNode(None, 'start')
    global_end = BoundaryNode(None, 'end')
    for e in events.values():
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
    q = deque([node for node, deg in indegree.items() if deg == 0])
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
    roots = [e for e in events.values() if not any(e in parent.children for parent in events.values())]

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

    return tree, events


def get_timeline(g,
                 drop_event_edges:bool,
                 rel_pos_tags:set,
                 temporal_relations_map:dict,
                 prefix:str):
  # get all temporal relations
  temp_relations = [[e[0], e[2]["labels"], e[1]]
                          for e in g.edges(data=True)
                          if "temp_" in e[2]["labels"]]
  for t in temp_relations:
    print(t)

  # get all event nodes
  nodes = ({e[0] for e in temp_relations})\
          .union({e[2] for e in temp_relations})

  # drop event edges if desired
  if drop_event_edges:
    for e in temp_relations:
      try:
        g.remove_edge(e[0], e[2])
      except Exception as ex:
        print(ex)
        print(e)

  timeline, evs = build_interval_timeline(
    event_names=nodes,
    temporal_relations_input=temp_relations,
    rel_pos_tags=rel_pos_tags,
    temporal_relations_map=temporal_relations_map,
    prefix=prefix
  )

  return timeline