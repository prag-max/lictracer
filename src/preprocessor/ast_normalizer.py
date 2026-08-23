# -*- coding: utf-8 -*-
"""预处理层：AST 解析与标识符归一。

- 使用 tree-sitter(-python) 解析 AST，把所有 identifier 节点替换为 ``VAR_n``，
  把 function_definition 的 name 替换为 ``FUNC_n``，并去除注释节点；
- 若 tree-sitter 不可用，退化到纯正则实现（去注释 + 标识符替换），保证不崩溃；
- 返回值是纯结构骨架文本（保留原始换行与缩进，便于后续相似度召回）。

线程安全：``tree_sitter.Parser`` 非线程安全（共享内部缓冲区），故每个线程
通过 ``threading.local`` 持有独立 parser，避免 FastAPI 线程池并发解析的数据竞争。
"""
from __future__ import annotations

import logging
import re
import threading
import zlib

logger = logging.getLogger("lictracer.preprocessor")

# ---------- tree-sitter 加载（失败则置空，走正则兜底） ----------
try:
    import tree_sitter  # type: ignore
    import tree_sitter_python  # type: ignore

    _TS_LANGUAGE = tree_sitter.Language(tree_sitter_python.language())
    _TS_AVAILABLE = True
except Exception:
    _TS_LANGUAGE = None
    _TS_AVAILABLE = False
    logger.warning("tree-sitter 不可用，预处理将降级为正则实现", exc_info=True)

# 每线程独立 parser（tree_sitter.Parser 非线程安全）
_TS_LOCAL = threading.local()


def _get_parser():
    """返回当前线程的 parser；tree-sitter 不可用时返回 None。"""
    if not _TS_AVAILABLE:
        return None
    parser = getattr(_TS_LOCAL, "parser", None)
    if parser is None:
        parser = tree_sitter.Parser(_TS_LANGUAGE)
        _TS_LOCAL.parser = parser
    return parser


def tree_sitter_available() -> bool:
    """tree-sitter 是否可用（供报告 methodology 字段标识降级状态）。"""
    return _get_parser() is not None


def _walk(root):
    """深度优先遍历 AST 节点。"""
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        # type_/ 兼容不同 tree-sitter 版本的子节点访问方式
        children = getattr(node, "children", None)
        if children is None:
            children = getattr(node, "named_children", None)
        if children:
            stack.extend(children)


def _normalize_tree_sitter(code: str) -> str:
    """tree-sitter 解析实现：标识符归一 + 去注释（基于字节偏移操作，兼容中文）。"""
    parser = _get_parser()
    if parser is None:
        raise RuntimeError("tree-sitter 不可用")
    raw = code.encode("utf-8")
    tree = parser.parse(raw)
    root = tree.root_node

    # 收集函数名字节点的字节区间（用于区分 FUNC 与 VAR）
    func_name_ranges = set()
    comment_ranges = []
    identifier_nodes = []
    for node in _walk(root):
        node_type = node.type
        if node_type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node is not None:
                func_name_ranges.add((name_node.start_byte, name_node.end_byte))
        elif node_type == "comment":
            comment_ranges.append((node.start_byte, node.end_byte))
        elif node_type == "identifier":
            identifier_nodes.append(node)

    identifier_nodes.sort(key=lambda n: (n.start_byte, n.end_byte))

    # 构造编辑序列（替换/删除），保证字节区间不重叠
    edits = []  # (start, end, replacement_bytes)
    edits.extend((s, e, b"") for s, e in comment_ranges)
    var_counter = 0
    func_counter = 0
    for node in identifier_nodes:
        key = (node.start_byte, node.end_byte)
        if key in func_name_ranges:
            text = "FUNC_%d" % func_counter
            func_counter += 1
        else:
            text = "VAR_%d" % var_counter
            var_counter += 1
        edits.append((node.start_byte, node.end_byte, text.encode("utf-8")))

    edits.sort(key=lambda x: (x[0], x[1]))

    # 按偏移拼接，替换/删除指定区间
    out = bytearray()
    pos = 0
    for start, end, repl in edits:
        if start < pos:  # 区间重叠保护（正常情况下不会发生）
            continue
        out.extend(raw[pos:start])
        out.extend(repl)
        pos = end
    out.extend(raw[pos:])
    return out.decode("utf-8")


# 正则兜底所用的 Python 关键字（避免把关键字误替换）
_PY_KEYWORDS = {
    "def", "return", "import", "from", "as", "class", "if", "else", "elif",
    "for", "while", "in", "not", "and", "or", "is", "None", "True", "False",
    "with", "try", "except", "finally", "raise", "pass", "global", "nonlocal",
    "lambda", "yield", "del", "assert", "async", "await", "break", "continue",
}

# 公开别名（供确定性等价验证器等下游做行级 token 规范化）
PY_KEYWORDS = _PY_KEYWORDS


def _normalize_regex(code: str) -> str:
    """纯正则兜底：去除 ``#`` 注释 + 标识符归一。"""
    # 去除行内注释（简化处理，不解析字符串内 '#'）
    lines = [re.sub(r"#[^\n]*", "", ln).rstrip() for ln in code.split("\n")]
    text = "\n".join(lines)

    # 函数名归一：def name -> def FUNC_n
    func_counter = [0]

    def _func_repl(m: "re.Match") -> str:
        name = "FUNC_%d" % func_counter[0]
        func_counter[0] += 1
        return "def " + name

    text = re.sub(r"\bdef[ \t]+[A-Za-z_]\w*", _func_repl, text)

    # 其余标识符归一为 VAR_n
    var_counter = [0]

    def _ident_repl(m: "re.Match") -> str:
        tok = m.group(0)
        if tok in _PY_KEYWORDS or tok.startswith("FUNC_") or tok.startswith("VAR_"):
            return tok
        name = "VAR_%d" % var_counter[0]
        var_counter[0] += 1
        return name

    text = re.sub(r"\b[A-Za-z_]\w*\b", _ident_repl, text)
    return text


def normalize(code: str) -> str:
    """把 Python 源码规范化为结构骨架文本（标识符归一、去注释）。"""
    if not code:
        return ""
    if tree_sitter_available():
        try:
            return _normalize_tree_sitter(code)
        except Exception:
            pass
    return _normalize_regex(code)


def original_lines(code: str) -> "list[str]":
    """返回原代码的行列表，供下游行级证据使用。"""
    return code.splitlines()


def ast_statement_sequences(code: str) -> "tuple[list, list, list, bool]":
    """提取规范化语句哈希序列（供确定性等价验证器做结构包含判定）。

    对每个语句节点计算规范化子树哈希：identifier→``ID``、integer/float→``NUM``、
    string→``STR`` 占位（重命名 / 常量改写不变），关键字与运算符保留实际文本，
    注释节点跳过——与 ``normalize`` 去注释语义一致。

    返回 ``(module_stmts, funcs, classes, parsed_ok)``：
    - ``module_stmts``：``[(hash, start_line, end_line), ...]`` 模块级语句
      （import / 顶层赋值 / 类定义 / 函数定义 等，供模块级结构克隆判定）；
    - ``funcs``：``[{"start": 函数起行, "end": 函数止行,
      "stmts": [(hash, start_line, end_line), ...]}, ...]``，**仅模块级函数**
      （类内方法由类体结构序列 L2b 覆盖；嵌套函数作为父函数体的语句哈希参与——
      排除短方法体 / 嵌套函数体，防单语句过度匹配升级为 L2 强证据），
      行号为 1-based 源码行；
    - ``classes``：``[{"start", "end", "name", "stmts": [...]}, ...]``，每个
      ``class_definition`` 的类体**结构**指纹序列——仅含类属性赋值与方法**签名**
      （``def name(params)``，含方法名与参数结构、不含方法体——方法名参与哈希
      以消除同参数结构方法的碰撞，使「复制一个配置 / Dataclass 类」能被保序
      包含匹配（类属性克隆）且不因方法体改写而跌出；方法名重命名跌出 L2b，
      由 L3 锚点兜底），
    - ``parsed_ok``：tree-sitter 可用且解析成功。解析失败 / 不可用返回
      ``([], [], [], False)``，调用方降级为仅使用 L1/L3。
    """
    parser = _get_parser()
    if parser is None:
        return [], [], [], False
    try:
        raw = code.encode("utf-8")
        tree = parser.parse(raw)
    except Exception:
        return [], [], [], False

    # 字节偏移 → 1-based 行号（bisect 到换行位置列表）
    newlines = [i for i, b in enumerate(raw) if b == 10]

    def _line_of(byte_pos: int) -> int:
        import bisect

        return bisect.bisect_right(newlines, byte_pos) + 1

    memo = {}

    def _h(s: str) -> int:
        return zlib.crc32(s.encode("utf-8"))

    def _leaf_descriptor(node) -> str:
        t = node.type
        if t == "identifier":
            return "ID"
        if t in ("integer", "float"):
            return "NUM"
        if t in ("string", "concatenated_string", "bytes"):
            return "STR"
        try:
            text = raw[node.start_byte : node.end_byte].decode(
                "utf-8", errors="replace"
            )
        except Exception:
            text = ""
        return f"{t}:{text}"

    def _stmt_hash(node) -> "int | None":
        if node.type == "comment":
            return None
        key = (node.start_byte, node.end_byte, node.type)
        cached = memo.get(key)
        if cached is not None:
            return cached
        children = getattr(node, "children", None)
        if children is None:
            children = getattr(node, "named_children", None)
        if children:
            child_hashes = []
            for c in children:
                hh = _stmt_hash(c)
                if hh is not None:
                    child_hashes.append(hh)
            desc = node.type + "(" + ",".join(str(h) for h in child_hashes) + ")"
        else:
            desc = _leaf_descriptor(node)
        h = _h(desc)
        memo[key] = h
        return h

    def _statement_sequence(parent) -> "list":
        seq = []
        children = getattr(parent, "named_children", None)
        if children is None:
            children = getattr(parent, "children", None)
        for c in children or []:
            h = _stmt_hash(c)
            if h is not None:
                seq.append((h, _line_of(c.start_byte), _line_of(c.end_byte - 1)))
        return seq

    def _def_signature_hash(node) -> int:
        """函数 / 方法签名哈希：``def name(params)``，含**方法名**与参数结构、
        不含方法体。

        方法名必须参与哈希：若只哈希参数结构，所有无参方法（``def f(self):``
        等）哈希完全相同——任意类的无参方法序列会互相「保序匹配」，导致 L2b
        类体伪匹配泛滥（真实大类中数十个无参方法同哈希）。代价：方法名重命名
        的类克隆跌出 L2 结构匹配（由 L3 锚点行游程兜底，诚实边界见验证器文档）。
        """
        name = node.child_by_field_name("name")
        nm = ""
        if name is not None:
            nm = raw[name.start_byte : name.end_byte].decode("utf-8", errors="replace")
        params = node.child_by_field_name("parameters")
        ph = _stmt_hash(params) if params else 0
        return _h("def(" + nm + str(ph) + ")")

    def _is_docstring(node) -> bool:
        if node.type != "expression_statement":
            return False
        inner = getattr(node, "children", None)
        if not inner:
            return False
        return inner[0].type in ("string", "concatenated_string")

    def _attr_hash(node) -> int:
        """类属性赋值哈希：保留左值属性名（提高特异性、防简单赋值类误报），

        右值仍规范化（ID/NUM/STR）。复制配置类通常保留属性名、仅改名类名 /
        方法名，故类属性克隆在容忍类名/方法名重命名的同时保持高特异性。
        """
        left = node.child_by_field_name("left")
        name = ""
        if left is not None:
            name = raw[left.start_byte : left.end_byte].decode("utf-8", errors="replace")
        right = node.child_by_field_name("right")
        rh = _stmt_hash(right) if right else 0
        return _h("attr(" + name + "," + str(rh) + ")")

    def _class_struct_seq(node) -> "list":
        """类体结构指纹序列：类属性赋值 + 方法签名（+ 嵌套类签名）。"""
        seq: list = []
        body = node.child_by_field_name("body")
        if body is None:
            return seq
        children = getattr(body, "named_children", None)
        if children is None:
            children = getattr(body, "children", None)
        for c in children or []:
            if c.type == "comment" or _is_docstring(c):
                continue
            if c.type == "function_definition":
                h = _def_signature_hash(c)
            elif c.type == "class_definition":
                h = _h("class(" + ",".join(str(x) for x in _class_struct_seq(c)) + ")")
            else:
                if c.type in ("assignment", "augmented_assignment", "annotated_assignment"):
                    h = _attr_hash(c)
                else:
                    h = _stmt_hash(c)
            if h is None:
                continue
            seq.append((h, _line_of(c.start_byte), _line_of(c.end_byte - 1)))
        return seq

    try:
        root = tree.root_node
        module_stmts = _statement_sequence(root)
        funcs = []
        classes = []
        for node in _walk(root):
            if node.type == "function_definition":
                # 仅模块级函数进入 funcs（L2a 函数体包含判定）：类内方法由类体
                # 结构序列（L2b，方法签名哈希）覆盖；嵌套函数作为父函数体的语句
                # 哈希参与——若把短方法体/嵌套函数体也收为 funcs，其 1–3 语句
                # 的 needle 会与任意含该通用语句序列的函数匹配（单语句过度匹配
                # 升级为 L2 强证据，真实大类中无参/短方法大量存在，伪匹配泛滥）。
                p = node.parent
                inside = False
                while p is not None:
                    if p.type in ("class_definition", "function_definition"):
                        inside = True
                        break
                    p = p.parent
                if inside:
                    continue
                body = node.child_by_field_name("body")
                if body is None:
                    continue
                seq = _statement_sequence(body)
                if seq:
                    funcs.append(
                        {
                            "start": _line_of(node.start_byte),
                            "end": _line_of(node.end_byte - 1),
                            "stmts": seq,
                        }
                    )
            elif node.type == "class_definition":
                cseq = _class_struct_seq(node)
                if cseq:
                    name_node = node.child_by_field_name("name")
                    name = (
                        raw[name_node.start_byte : name_node.end_byte].decode(
                            "utf-8", errors="replace"
                        )
                        if name_node
                        else ""
                    )
                    classes.append(
                        {
                            "start": _line_of(node.start_byte),
                            "end": _line_of(node.end_byte - 1),
                            "name": name,
                            "stmts": cseq,
                        }
                    )
        return module_stmts, funcs, classes, True
    except RecursionError:
        return [], [], [], False
