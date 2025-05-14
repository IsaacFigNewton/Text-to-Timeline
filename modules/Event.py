from BoundaryNode import BoundaryNode

# Event with potential children (containment)
class Event:
    def __init__(self, name):
        self.name = name
        self.start = BoundaryNode(self, 'start')
        self.end = BoundaryNode(self, 'end')
        self.children = []

    # assumes each event has a unique id
    def __eq__(self, other):
        return self.name == other.name

    # assumes each event has a unique id
    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return f"{self.name}"