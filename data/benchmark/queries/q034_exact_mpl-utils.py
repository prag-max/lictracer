# 源自某 MPL-2.0 工具库：数值钳制
def clamp(value, low, high):
    return max(low, min(value, high))
