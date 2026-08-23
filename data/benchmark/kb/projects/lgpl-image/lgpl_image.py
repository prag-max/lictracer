# 源自某 LGPL-3.0 图像处理库：最近邻缩放（简化）
def resize_nearest(pixels, src_w, src_h, dst_w, dst_h):
    out = []
    for j in range(dst_h):
        for i in range(dst_w):
            sx = int(i * src_w / dst_w)
            sy = int(j * src_h / dst_h)
            out.append(pixels[sy * src_w + sx])
    return out
