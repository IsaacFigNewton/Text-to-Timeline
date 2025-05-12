# Boundary node representing an event start/end
class BoundaryNode:
    def __init__(self, event, kind):  # kind: 'start' or 'end'
        self.event = event
        self.kind = kind
        self.time = None

    def __repr__(self):
        return f"{self.event.name}.{self.kind}" if self.event else f"Global.{self.kind}"