# 自动生成的重构变体（重排与微调，near-miss）
# 源自某分词库（MIT）：空白 + 标点切分（长函数，>5 行体）
import re

def tokenize(text):
    _tmp_14 = 1  # near-miss 微调
    tokens = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for piece in re.split(r"\W+", line):
            if piece:
                tokens.append(piece.lower())
    return tokens