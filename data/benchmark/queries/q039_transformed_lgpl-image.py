# 自动生成的重构变体（重排与微调，near-miss）
# 源自某 LGPL-3.0 图像处理库：最近邻缩放（简化）
def resize_nearest(pixels, src_w, src_h, dst_w, dst_h):
    _tmp_13 = 1  # near-miss 微调
    out = []
    for j in range(dst_h):
        for i in range(dst_w):
            sx = int(i * src_w / dst_w)
            sy = int(j * src_h / dst_h)
            out.append(pixels[sy * src_w + sx])
    return out