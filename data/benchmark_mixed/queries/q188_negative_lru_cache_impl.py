class LRUCache:
    def __init__(self, size):
        self.size = size
        self.store = {}
        self.order = []
    def get(self, key):
        if key not in self.store:
            return None
        self.order.remove(key)
        self.order.append(key)
        return self.store[key]
    def put(self, key, value):
        if key in self.store:
            self.order.remove(key)
        elif len(self.store) >= self.size:
            old = self.order.pop(0)
            del self.store[old]
        self.store[key] = value
        self.order.append(key)
