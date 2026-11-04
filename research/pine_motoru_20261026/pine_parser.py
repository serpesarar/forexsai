"""Pine Script (v4/v5/v6) lexer + parser → AST.

AST düğümleri sade sınıflardır (Node.kind + alanlar). Amaç TradingView topluluk scriptlerinin çalıştırılması için
yeterli sözdizimi kapsamı; derleyici hata mesajlarının birebir kopyası değil.
"""
from __future__ import annotations

import re

# ── lexer ────────────────────────────────────────────────────────────────────
TOKEN_RE = re.compile(r"""
    (?P<ws>[ \t]+)
  | (?P<comment>//[^\n]*)
  | (?P<nl>\r?\n)
  | (?P<color>\#[0-9a-fA-F]{8}\b|\#[0-9a-fA-F]{6}\b|\#[0-9a-fA-F]{3}\b)
  | (?P<num>(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)
  | (?P<str>"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')
  | (?P<id>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<op>:=|=>|==|!=|<=|>=|\+=|-=|\*=|/=|%=|[-+*/%<>=?:,()\[\].])
""", re.X)

KEYWORDS = {"if", "else", "for", "while", "switch", "var", "varip", "and", "or", "not",
            "true", "false", "na", "break", "continue"}
SOFT = {"import", "as", "export", "method", "type", "enum", "to", "by", "in"}   # bağlama göre anahtar kelime


class Tok:
    __slots__ = ("k", "v", "line")

    def __init__(self, k, v, line):
        self.k, self.v, self.line = k, v, line

    def __repr__(self):
        return f"{self.k}:{self.v!r}@{self.line}"


class PineSyntaxError(Exception):
    pass


def _indent_width(s: str) -> int:
    return sum(4 if ch == "\t" else 1 for ch in s)


def _join_strings(src: str) -> str:
    """Satır sonuna taşan dizgeleri ve \'\'\'…\'\'\' bloklarını tek satıra indir; yorum içindeki tırnakları atla."""
    out, i, n = [], 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "/" and src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(src[i:j])
            i = j
            continue
        if ch in "'\"":
            triple = src.startswith(ch * 3, i)
            q = ch
            i += 3 if triple else 1
            buf = []
            while i < n:
                c = src[i]
                if c == "\\" and i + 1 < n:
                    buf.append(src[i:i + 2])
                    i += 2
                    continue
                if triple and src.startswith(q * 3, i):
                    i += 3
                    break
                if not triple and c == q:
                    i += 1
                    break
                if c == "\n":
                    buf.append(" ")
                    i += 1
                    while i < n and src[i] in " \t":
                        i += 1
                    continue
                if triple and c == q:
                    buf.append("\\" + q)
                    i += 1
                    continue
                buf.append(c)
                i += 1
            out.append(q + "".join(buf) + q)
            continue
        out.append(ch)
        i += 1
    return "".join(out)


_NOT_IN_TYPE = {"and", "or", "not", "if", "else", "for", "while", "switch", "true", "false", "na"}  # jenerik tipte olmaz
_DANGLING_OPS = {"+", "-", "*", "/", "%", "?", ":", ",", "==", "!=", "<", ">", "<=", ">="}


def _dangling(t) -> bool:
    """Satırı yarım bırakan belirteç (ikili operatör/virgül) → sonraki satır devam satırıdır."""
    return (t.k == "op" and t.v in _DANGLING_OPS) or (t.k == "kw" and t.v in ("and", "or"))


def lex(src: str) -> list[Tok]:
    """Mantıksal satırlar + INDENT/DEDENT. Parantez içinde ve 4'ün katı olmayan girintide satır devam eder."""
    src = _join_strings(src.replace("\r\n", "\n").replace("\r", "\n"))
    lines = src.split("\n")
    toks: list[Tok] = []
    stack = [0]
    depth = 0
    for ln, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("//"):
            continue
        ind = _indent_width(raw[: len(raw) - len(raw.lstrip())])
        cont = depth > 0 or (ind % 4 != 0) or (ind > stack[-1] and toks and _dangling(toks[-1]))
        if not cont:
            if toks and toks[-1].k != "NL":
                toks.append(Tok("NL", None, ln))
            if ind > stack[-1]:
                stack.append(ind)
                toks.append(Tok("INDENT", None, ln))
            while ind < stack[-1]:
                stack.pop()
                toks.append(Tok("DEDENT", None, ln))
            if ind != stack[-1]:
                raise PineSyntaxError(f"girinti hatası satır {ln}")
        pos = 0
        body = raw
        while pos < len(body):
            m = TOKEN_RE.match(body, pos)
            if not m:
                raise PineSyntaxError(f"tanınmayan karakter {body[pos]!r} satır {ln}")
            kind = m.lastgroup
            text = m.group(kind)
            pos = m.end()
            if kind in ("ws", "comment"):
                continue
            if kind == "id" and text in KEYWORDS:
                toks.append(Tok("kw", text, ln))
            elif kind == "op":
                if text in "([":
                    depth += 1
                elif text in ")]":
                    depth = max(0, depth - 1)
                toks.append(Tok("op", text, ln))
            else:
                toks.append(Tok(kind, text, ln))
    toks.append(Tok("NL", None, len(lines)))
    while len(stack) > 1:
        stack.pop()
        toks.append(Tok("DEDENT", None, len(lines)))
    toks.append(Tok("EOF", None, len(lines)))
    return toks


# ── AST ─────────────────────────────────────────────────────────────────────
class Node:
    __slots__ = ("kind", "a", "line")

    def __init__(self, kind, line=0, **a):
        self.kind, self.a, self.line = kind, a, line

    def __getattr__(self, k):
        try:
            return object.__getattribute__(self, "a")[k]
        except KeyError:
            raise AttributeError(k)

    def __repr__(self):
        return f"{self.kind}({', '.join(f'{k}={v!r}' for k, v in self.a.items())})"


TYPE_WORDS = {"int", "float", "bool", "string", "color", "line", "label", "box", "table", "linefill", "polyline",
              "array", "matrix", "map", "series", "simple", "const", "input", "chart"}
QUALIFIERS = {"series", "simple", "const", "input"}


class Parser:
    def __init__(self, toks: list[Tok]):
        self.t = toks
        self.i = 0
        self.udts: set[str] = set()

    # yardımcılar
    def peek(self, o=0) -> Tok:
        return self.t[min(self.i + o, len(self.t) - 1)]

    def next(self) -> Tok:
        tok = self.t[self.i]
        self.i += 1
        return tok

    def at(self, k, v=None, o=0) -> bool:
        tok = self.peek(o)
        return tok.k == k and (v is None or tok.v == v)

    def accept(self, k, v=None):
        if self.at(k, v):
            return self.next()
        return None

    def expect(self, k, v=None) -> Tok:
        if not self.at(k, v):
            tok = self.peek()
            raise PineSyntaxError(f"beklenen {k} {v!r}, bulunan {tok.k} {tok.v!r} satır {tok.line}")
        return self.next()

    def skip_nl(self):
        while self.at("NL"):
            self.next()

    # program
    def program(self) -> Node:
        body = []
        self.skip_nl()
        while not self.at("EOF"):
            if self.accept("DEDENT") or self.accept("INDENT"):
                continue
            body.append(self.statement())
            while self.accept("op", ","):
                if self.at("NL"):
                    break
                body.append(self.statement())
            self.skip_nl()
        return Node("program", body=body)

    def block(self) -> list[Node]:
        """NL INDENT stmt* DEDENT  ya da aynı satırda tek ifade."""
        if not self.at("NL"):
            body = [self.statement()]
            while self.accept("op", ","):
                if self.at("NL"):
                    break
                body.append(self.statement())
            return body
        self.skip_nl()
        self.expect("INDENT")
        body = []
        self.skip_nl()
        while not self.at("DEDENT") and not self.at("EOF"):
            body.append(self.statement())
            while self.accept("op", ","):
                if self.at("NL"):
                    break
                body.append(self.statement())
            self.skip_nl()
        self.accept("DEDENT")
        return body

    # deyimler
    def statement(self) -> Node:
        tok = self.peek()
        line = tok.line
        if tok.k == "id" and tok.v in SOFT:
            nxt = self.peek(1)
            if tok.v == "import" and nxt.k == "id" and not (nxt.k == "op"):
                return self.import_stmt()
            if tok.v == "export" and (nxt.k in ("id", "kw")) and not self.at("op", "=", 1):
                self.next()
                return self.statement()
            if tok.v in ("type", "enum") and nxt.k == "id" and self.peek(2).k == "NL":
                return self.type_def(tok.v)
            if tok.v == "method" and nxt.k == "id" and self.at("op", "(", 2):
                self.next()
                return self.func_def(method=True)
        if tok.k == "kw":
            if tok.v in ("var", "varip"):
                self.next()
                return self.declaration(mode=tok.v)
            if tok.v == "break":
                self.next()
                return Node("break", line)
            if tok.v == "continue":
                self.next()
                return Node("continue", line)
        if tok.k == "op" and tok.v == "[" and self._is_tuple_decl():
            return self.tuple_decl()
        if tok.k == "id" and self.at("op", "(", 1) and self._is_func_def():
            return self.func_def(method=False)
        if self._is_typed_decl():
            return self.declaration(mode=None)
        if tok.k == "id" and self.at("op", "=", 1):
            return self.declaration(mode=None)
        expr = self.expression()
        if self.peek().k == "op" and self.peek().v in (":=", "+=", "-=", "*=", "/=", "%="):
            op = self.next().v
            val = self.expression()
            return Node("assign", line, target=expr, op=op, value=val)
        return Node("expr", line, value=expr)

    def import_stmt(self) -> Node:
        line = self.next().line
        parts = []
        while not self.at("NL") and not self.at("id", "as"):
            parts.append(str(self.next().v))
        alias = None
        if self.accept("id", "as"):
            alias = self.next().v
        path = "".join(parts)
        if alias is None:
            alias = path.split("/")[1] if path.count("/") >= 1 else path
        return Node("import", line, path=path, alias=alias)

    def type_def(self, kw) -> Node:
        line = self.next().line
        name = self.expect("id").v
        self.udts.add(name)
        fields = []
        self.skip_nl()
        if self.accept("INDENT"):
            self.skip_nl()
            while not self.at("DEDENT") and not self.at("EOF"):
                if kw == "enum":
                    fname = self.next().v
                    title = None
                    if self.accept("op", "="):
                        title = self.expression()
                    fields.append((fname, None, title))
                else:
                    self.accept("kw", "varip")
                    ftype = self.type_expr()
                    fname = self.expect("id").v
                    default = self.expression() if self.accept("op", "=") else None
                    fields.append((fname, ftype, default))
                self.skip_nl()
            self.accept("DEDENT")
        return Node(kw, line, name=name, fields=fields)

    def _scan_close(self, j, opener, closer) -> int:
        depth = 0
        while j < len(self.t):
            tok = self.t[j]
            if tok.k == "op" and tok.v == opener:
                depth += 1
            elif tok.k == "op" and tok.v == closer:
                depth -= 1
                if depth == 0:
                    return j
            elif tok.k == "EOF":
                break
            j += 1
        return -1

    def _is_func_def(self) -> bool:
        j = self._scan_close(self.i + 1, "(", ")")
        return j > 0 and self.t[j + 1].k == "op" and self.t[j + 1].v == "=>"

    def _is_tuple_decl(self) -> bool:
        j = self._scan_close(self.i, "[", "]")
        return j > 0 and self.t[j + 1].k == "op" and self.t[j + 1].v in ("=", ":=")

    def _is_typed_decl(self) -> bool:
        """TYPE [<..>] ['[]'] IDENT '='  — tip kelimesi, UDT adı ya da kütüphane.Tip."""
        j = self.i
        tok = self.t[j]
        if tok.k not in ("id", "kw"):
            return False
        if tok.k == "id" and tok.v in QUALIFIERS:
            j += 1
            tok = self.t[j]
        if tok.k != "id":
            return False
        is_type = tok.v in TYPE_WORDS or tok.v in self.udts or (tok.v[:1].isupper())
        j += 1
        while self.t[j].k == "op" and self.t[j].v == "." and self.t[j + 1].k == "id":
            j += 2
            is_type = True
        if self.t[j].k == "op" and self.t[j].v == "<":
            depth = 0
            while j < len(self.t):
                if self.t[j].k == "op" and self.t[j].v == "<":
                    depth += 1
                elif self.t[j].k == "op" and self.t[j].v == ">":
                    depth -= 1
                    if depth == 0:
                        break
                elif self.t[j].k in ("NL", "EOF"):
                    return False
                j += 1
            j += 1
            is_type = True
        if self.t[j].k == "op" and self.t[j].v == "[" and self.t[j + 1].k == "op" and self.t[j + 1].v == "]":
            j += 2
            is_type = True
        return is_type and self.t[j].k == "id" and self.t[j + 1].k == "op" and self.t[j + 1].v == "="

    def type_expr(self) -> str:
        parts = []
        if self.at("id") and self.peek().v in QUALIFIERS and self.at("id", o=1):
            self.next()
        parts.append(self.expect("id").v)
        while self.at("op", ".") and self.at("id", o=1):
            self.next()
            parts.append("." + self.next().v)
        if self.at("op", "<"):
            depth = 0
            while True:
                tok = self.next()
                parts.append(str(tok.v))
                if tok.v == "<":
                    depth += 1
                elif tok.v == ">":
                    depth -= 1
                    if depth == 0:
                        break
        if self.at("op", "[") and self.at("op", "]", 1):
            self.next()
            self.next()
            parts.append("[]")
        return "".join(parts)

    def declaration(self, mode) -> Node:
        line = self.peek().line
        vtype = None
        if self._is_typed_decl():
            vtype = self.type_expr()
        name = self.expect("id").v
        self.expect("op", "=")
        value = self.expr_or_block()
        return Node("decl", line, name=name, mode=mode, vtype=vtype, value=value)

    def tuple_decl(self) -> Node:
        line = self.next().line
        names = []
        while not self.at("op", "]"):
            names.append(self.expect("id").v)
            self.accept("op", ",")
        self.expect("op", "]")
        op = self.next().v
        value = self.expr_or_block()
        return Node("tuple_decl", line, names=names, value=value, op=op)

    def params(self) -> list[tuple]:
        self.expect("op", "(")
        ps = []
        while not self.at("op", ")"):
            ptype = None
            if self._param_has_type():
                ptype = self.type_expr()
            pname = self.expect("id").v
            default = self.expression() if self.accept("op", "=") else None
            ps.append((pname, ptype, default))
            self.accept("op", ",")
        self.expect("op", ")")
        return ps

    def _param_has_type(self) -> bool:
        j = self.i
        n = 0
        while self.t[j].k in ("id",) or (self.t[j].k == "op" and self.t[j].v in ("<", ">", ",", "[", "]", ".")):
            if self.t[j].k == "op" and self.t[j].v == "," and n == 0:
                break
            if self.t[j].k == "op" and self.t[j].v == "<":
                n += 1
            if self.t[j].k == "op" and self.t[j].v == ">":
                n -= 1
            j += 1
            if self.t[j].k == "op" and self.t[j].v in ("=", ")") and n == 0:
                break
        span = self.t[self.i:j]
        ids = [tok for tok in span if tok.k == "id"]
        return len(ids) >= 2 and not (len(span) > 1 and span[1].k == "op" and span[1].v == "=")

    def func_def(self, method) -> Node:
        line = self.peek().line
        name = self.expect("id").v
        ps = self.params()
        self.expect("op", "=>")
        body = self.block()
        return Node("func", line, name=name, params=ps, body=body, method=method)

    def expr_or_block(self) -> Node:
        if self.at("kw", "if"):
            return self.if_expr()
        if self.at("kw", "switch"):
            return self.switch_expr()
        if self.at("kw", "for"):
            return self.for_expr()
        if self.at("kw", "while"):
            return self.while_expr()
        return self.expression()

    # kontrol yapıları (ifade olarak da kullanılabilir)
    def if_expr(self) -> Node:
        line = self.expect("kw", "if").line
        cond = self.expression()
        body = self.block()
        orelse = None
        save = self.i
        self.skip_nl()
        if self.accept("kw", "else"):
            if self.at("kw", "if"):
                orelse = [self.if_expr()]
            else:
                orelse = self.block()
        else:
            self.i = save
        return Node("if", line, cond=cond, body=body, orelse=orelse)

    def switch_expr(self) -> Node:
        line = self.expect("kw", "switch").line
        subject = None if self.at("NL") else self.expression()
        cases = []
        self.skip_nl()
        self.expect("INDENT")
        self.skip_nl()
        while not self.at("DEDENT") and not self.at("EOF"):
            if self.accept("op", "=>"):
                cases.append((None, self.block()))
            else:
                key = self.expression()
                self.expect("op", "=>")
                cases.append((key, self.block()))
            self.skip_nl()
        self.accept("DEDENT")
        return Node("switch", line, subject=subject, cases=cases)

    def for_expr(self) -> Node:
        line = self.expect("kw", "for").line
        if self.at("op", "["):
            self.next()
            i_name = self.expect("id").v
            self.expect("op", ",")
            v_name = self.expect("id").v
            self.expect("op", "]")
            self.expect("id", "in")
            coll = self.expression()
            return Node("forin", line, idx=i_name, var=v_name, coll=coll, body=self.block())
        if self.at("id") and self.at("id", o=1) and self.peek(1).v not in ("in",):
            self.next()                                   # tipli döngü değişkeni: for int i = ...
        var = self.next().v if (self.at("kw") and self.at("op", "=", 1)) else self.expect("id").v
        if self.accept("id", "in"):
            coll = self.expression()
            return Node("forin", line, idx=None, var=var, coll=coll, body=self.block())
        self.expect("op", "=")
        start = self.expression()
        self.expect("id", "to")
        end = self.expression()
        step = self.expression() if self.accept("id", "by") else None
        return Node("for", line, var=var, start=start, end=end, step=step, body=self.block())

    def while_expr(self) -> Node:
        line = self.expect("kw", "while").line
        cond = self.expression()
        return Node("while", line, cond=cond, body=self.block())

    # ifadeler (öncelik: ?: < or < and < == != < < > <= >= < + - < * / % < tekli < sonek)
    def expression(self) -> Node:
        if self.at("kw", "if"):
            return self.if_expr()
        if self.at("kw", "switch"):
            return self.switch_expr()
        if self.at("kw", "for"):
            return self.for_expr()
        cond = self.or_expr()
        if self.accept("op", "?"):
            a = self.expression()
            self.expect("op", ":")
            b = self.expression()
            return Node("ternary", cond.line, cond=cond, t=a, f=b)
        return cond

    def _binary(self, sub, ops, kind="bin"):
        left = sub()
        while (self.peek().k in ("op", "kw")) and self.peek().v in ops:
            op = self.next().v
            right = sub()
            left = Node(kind, left.line, op=op, l=left, r=right)
        return left

    def or_expr(self):
        return self._binary(self.and_expr, ("or",))

    def and_expr(self):
        return self._binary(self.eq_expr, ("and",))

    def eq_expr(self):
        return self._binary(self.cmp_expr, ("==", "!="))

    def cmp_expr(self):
        return self._binary(self.add_expr, ("<", ">", "<=", ">="))

    def add_expr(self):
        return self._binary(self.mul_expr, ("+", "-"))

    def mul_expr(self):
        return self._binary(self.unary, ("*", "/", "%"))

    def unary(self):
        tok = self.peek()
        if (tok.k == "op" and tok.v in ("-", "+")) or (tok.k == "kw" and tok.v == "not"):
            self.next()
            return Node("unary", tok.line, op=tok.v, x=self.unary())
        return self.postfix()

    def _generic_args(self) -> list[str] | None:
        """ad<tip,...>( kalıbı — '<' karşılaştırmasıyla karışmasın diye ileri bakış."""
        if not self.at("op", "<"):
            return None
        j, depth, args, cur = self.i, 0, [], ""
        while j < len(self.t):
            tok = self.t[j]
            if tok.k == "op" and tok.v == "<":
                depth += 1
                if depth > 1:
                    cur += "<"
            elif tok.k == "op" and tok.v == ">":
                depth -= 1
                if depth == 0:
                    break
                cur += ">"
            elif tok.k == "op" and tok.v == "," and depth == 1:
                args.append(cur)
                cur = ""
            elif tok.k == "id" or (tok.k == "kw" and tok.v not in _NOT_IN_TYPE) or \
                    (tok.k == "op" and tok.v in (".", "[", "]")):
                cur += str(tok.v)
            else:
                return None
            j += 1
        if j + 1 < len(self.t) and self.t[j + 1].k == "op" and self.t[j + 1].v == "(":
            args.append(cur)
            self.i = j + 1
            return args
        return None

    def postfix(self) -> Node:
        node = self.primary()
        if node.kind in ("if", "switch", "for", "forin", "while"):
            return node                                   # blok yapılı ifadeden sonra sonek yok
        while True:
            if self.at("op", "."):
                self.next()
                name = self.next().v
                node = Node("attr", node.line, obj=node, name=name)
            elif self.at("op", "("):
                node = self.call(node, None)
            elif self.at("op", "<") and node.kind in ("name", "attr"):
                g = self._generic_args()
                if g is None:
                    break
                node = self.call(node, g)
            elif self.at("op", "["):
                self.next()
                idx = self.expression()
                self.expect("op", "]")
                node = Node("hist", node.line, x=node, n=idx)
            else:
                break
        return node

    def call(self, fn, generic) -> Node:
        line = self.expect("op", "(").line
        args, kwargs = [], {}
        while not self.at("op", ")"):
            if (self.at("id") or self.at("kw")) and self.at("op", "=", 1):
                k = self.next().v
                self.next()
                kwargs[k] = self.expression()
            else:
                args.append(self.expression())
            if not self.accept("op", ","):
                break
        self.expect("op", ")")
        return Node("call", line, fn=fn, args=args, kwargs=kwargs, generic=generic)

    def primary(self) -> Node:
        tok = self.next()
        if tok.k == "num":
            v = float(tok.v) if any(ch in tok.v for ch in ".eE") else int(tok.v)
            return Node("num", tok.line, v=v)
        if tok.k == "str":
            body = tok.v[1:-1]
            body = body.encode("utf-8").decode("unicode_escape", errors="ignore") if "\\" in body else body
            return Node("str", tok.line, v=body)
        if tok.k == "color":
            return Node("color", tok.line, v=tok.v)
        if tok.k == "kw" and tok.v in ("true", "false"):
            return Node("bool", tok.line, v=tok.v == "true")
        if tok.k == "kw" and tok.v == "na":
            return Node("na", tok.line)
        if tok.k == "id":
            return Node("name", tok.line, id=tok.v)
        if tok.k == "op" and tok.v == "(":
            e = self.expression()
            self.expect("op", ")")
            return e
        if tok.k == "op" and tok.v == "[":
            items = []
            while not self.at("op", "]"):
                items.append(self.expression())
                if not self.accept("op", ","):
                    break
            self.expect("op", "]")
            return Node("tuple", tok.line, items=items)
        if tok.k == "kw" and tok.v in ("if", "switch", "for", "while"):
            self.i -= 1
            return self.expr_or_block()
        raise PineSyntaxError(f"beklenmeyen {tok.k} {tok.v!r} satır {tok.line}")


def parse(src: str) -> Node:
    return Parser(lex(src)).program()


def version_of(src: str) -> int:
    m = re.search(r"//\s*@version\s*=\s*(\d+)", src)
    return int(m.group(1)) if m else 1
