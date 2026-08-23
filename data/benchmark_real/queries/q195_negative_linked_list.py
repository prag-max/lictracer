class Node:
    def __init__(self, val):
        self.val = val
        self.next = None

def to_list(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out
