from BoundaryNode import BoundaryNode

# Event with potential children (containment)
class Event:
    def __init__(self, name):
        self.name = name
        self.start = BoundaryNode(self, 'start')
        self.end = BoundaryNode(self, 'end')
        self.children = []

    def __str__(self):
        return f"{self.name}"