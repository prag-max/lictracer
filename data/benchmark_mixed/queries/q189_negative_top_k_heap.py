import heapq

def top_k(items, k):
    heap = []
    for it in items:
        heapq.heappush(heap, it)
        if len(heap) > k:
            heapq.heappop(heap)
    return sorted(heap, reverse=True)
