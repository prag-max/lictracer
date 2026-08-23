# 源自某分词库（MIT）：空白 + 标点切分（长函数，>5 行体）
import re

def func14(arg0):
    tokens = []
    for line in arg0.splitlines():
        line = line.strip()
        if not line:
            continue
        for piece in re.split(r"\W+", line):
            if piece:
                tokens.append(piece.lower())
    return tokens