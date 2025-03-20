class InMemoryEventStore:
    def __init__(self):
        self.events = {}

    def append(self, process_id, event):
        if process_id not in self.events:
            self.events[process_id] = []
        self.events[process_id].append(event)

    def get(self, process_id):
        return self.events.get(process_id, [])
