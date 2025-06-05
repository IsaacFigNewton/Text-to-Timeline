from .BoundaryNode import BoundaryNode

# Event with potential children (containment)
class Event:
    def __init__(self, id):
        self.id = id
        self.start = BoundaryNode(self, 'start')
        self.end = BoundaryNode(self, 'end')
        self.children = []

    # assumes each event has a unique id
    def __eq__(self, other):
        return self.id == other.id

    # assumes each event has a unique id
    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return f"{self.id}"