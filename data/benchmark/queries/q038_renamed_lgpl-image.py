# 源自某 LGPL-3.0 图像处理库：最近邻缩放（简化）
def func13(arg0, arg1, arg2, arg3, arg4):
    out = []
    for j in range(arg4):
        for i in range(arg3):
            sx = int(i * arg1 / arg3)
            sy = int(j * arg2 / arg4)
            out.append(arg0[sy * arg1 + sx])
    return out