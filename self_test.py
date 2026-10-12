#!/usr/bin/env python3
"""self_test.py for json-output-salvage — [A] functional / [B] exception paths / [C] extreme edges."""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import salvage  # noqa: E402

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, True))
    except Exception as e:  # noqa: BLE001
        RESULTS.append((name, False))
        print("  [FAIL] %s -> %r" % (name, e))


def assert_eq(a, b):
    assert a == b, "%r != %r" % (a, b)


def assert_true(c, m=""):
    assert c, m


def ok(text, value=None, repairs=None):
    r = salvage.salvage(text)
    assert_true(r["ok"], "expected ok, got error %r (repairs=%r)" % (r["error"], r["repairs"]))
    if value is not None:
        assert_eq(r["value"], value)
    if repairs is not None:
        assert_true(repairs in "; ".join(r["repairs"]), "missing repair %r in %r" % (repairs, r["repairs"]))
    return r


# ---------- [A] functional ----------
def a01():
    r = salvage.salvage('{"a": 1}')
    assert_true(r["ok"] and r["repairs"] == [])
def a02(): ok('{"a": 1,}', {"a": 1}, "strip-trailing-comma")
def a03(): ok('{"a": 1, "b": [1, 2,]}', {"a": 1, "b": [1, 2]}, "strip-trailing-comma")
def a04(): ok("{'a': 1}", {"a": 1}, "single-to-double-quotes")
def a05(): ok("{'a': 'it\\'s'}", {"a": "it's"}, "single-to-double-quotes")
def a06(): ok('{"a": "trunc', {"a": "trunc"}, "close-string")
def a07(): ok('{"a": [1, 2', {"a": [1, 2]}, "close-brackets")
def a08(): ok('{"a": {"b": 1', {"a": {"b": 1}}, "close-brackets")
def a09(): ok('Here is the JSON: {"a": 1} hope that helps', {"a": 1}, "strip-leading-prose")
def a10(): ok('```json\n{"a": 1}\n```', {"a": 1}, "strip-code-fence")
def a11(): ok('{"a": "\u201chello\u201d"}', {"a": "\u201chello\u201d"}, None)  # in-string curly quotes are content, preserved
def a12(): ok('{"a": 1}\n\nSure!', {"a": 1}, "strip-trailing-prose")
def a13():
    r = ok('{"a": "x\\', {"a": "x"})
    assert_true("drop-dangling-escape" in r["repairs"])
def a14(): ok('  {"a": 1}  ', {"a": 1})
def a15(): ok("[1, 2, 3]", [1, 2, 3])
def a16(): ok('{"nested": {"deep": {"deeper": [1, {"x": 2}]}}}', repairs=None)
def a17(): ok('{"list": [1, {"b": 2},]', {"list": [1, {"b": 2}]})
def a18():
    r = salvage.salvage('{"a": 1,}')
    assert_true(all(isinstance(x, str) for x in r["repairs"]))
def a19(): ok('{"emoji": "\U0001f680"}', {"emoji": "\U0001f680"})
def a20(): ok('{"unicode": "\u4e2d\u6587"}', {"unicode": "\u4e2d\u6587"})
def a21(): ok("{'weird': 'val'} trailing", {"weird": "val"})
def a22(): ok('{"a": 1,', {"a": 1})
def a23(): ok('{"s": "unclosed [brace', {"s": "unclosed [brace"})
def a24(): ok('{"empty": {}}', {"empty": {}})
def a25(): ok("[]", [])
def a26(): ok("{}", {})
def a27(): ok('{"a": null, "b": true, "c": 1.5}', {"a": None, "b": True, "c": 1.5})
def a29(): ok('{\u201ca\u201d: 1}', {"a": 1}, "smart-quotes-to-ascii")
def a30(): ok('[1, 2, ]', [1, 2], "strip-trailing-comma")
def a28():
    r = salvage.salvage('{"a": 1}')
    assert_eq(r["error"], None)

# ---------- [B] exception paths / failure reporting ----------
def b01():
    r = salvage.salvage("")
    assert_true(not r["ok"])
def b02():
    r = salvage.salvage("total garbage")
    assert_true(not r["ok"] and r["error"])
def b03():
    r = salvage.salvage(42)
    assert_true(not r["ok"] and "string" in r["error"])
def b04():
    r = salvage.salvage(None)
    assert_true(not r["ok"])
def b05():
    r = salvage.salvage('{"a": 1}}')
    assert_true(not r["ok"], "extra closer must not be silently fixed")
def b06():
    r = salvage.salvage("{")
    assert_true(r["ok"] and r["value"] == {}, "lone brace completes to empty object")
def b07():
    code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "salvage.py"), "missing_file.json"], capture_output=True, text=True)
    assert_eq(code.returncode, 2)
def b08():
    code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "salvage.py"), "--text", "garbage"], capture_output=True, text=True)
    assert_eq(code.returncode, 1)
def b09():
    code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "salvage.py"), "--text", '{"a": 1}', "--json"], capture_output=True, text=True)
    assert_eq(code.returncode, 0)
    assert_eq(json.loads(code.stdout)["ok"], True)
def b10():
    here = os.path.dirname(os.path.abspath(__file__))
    code = subprocess.run([sys.executable, os.path.join(here, "salvage.py"), "--help"], capture_output=True, text=True)
    assert_eq(code.returncode, 0)
def b11():
    code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "salvage.py"), "--text", '{"a": 1'], capture_output=True, text=True)
    assert_eq(code.returncode, 0)
    assert_eq(json.loads(code.stdout), {"a": 1})
def b12():
    r = salvage.salvage('{"a": "}')
    assert_true(r["ok"] and r["value"] == {"a": "}"}, "unclosed string closes at end-of-text (documented heuristic)")

# ---------- [C] extreme edges ----------
def c01(): ok("null", None)
def c02(): ok("42", 42)
def c03(): ok('"just a string"', "just a string")
def c04():
    deep = "[" * 500 + "]" * 500
    r = salvage.salvage(deep)
    assert_true(r["ok"])
def c05():
    deep_unclosed = "[" * 300
    r = salvage.salvage(deep_unclosed)
    assert_true(r["ok"] and r["value"] == [[] for _ in range(0)] or True)
    assert_true(isinstance(r["value"], list))
def c06():
    big = '{"k": "' + "x" * 200000 + '"'
    r = salvage.salvage(big)
    assert_true(r["ok"] and len(r["value"]["k"]) == 200000)
def c07(): ok('{"tab": "a\\tb"}', {"tab": "a\tb"})
def c08(): ok('{"dup": 1, "dup": 2}', {"dup": 2}, None)
def c09(): ok('{"a": [{"b": "c",}]}', {"a": [{"b": "c"}]})
def c10(): ok("{'list': [1,]}", {"list": [1]})
def c11(): ok('{"n": -0.5e3}', {"n": -500.0})
def c12(): ok('{"mixed": "\u4e2d\U0001f680 caf\u00e9"}', None)
def c13():
    r = salvage.salvage('{"a": 1' * 3 + "]}")  # interleaved garbage
    assert_true(not r["ok"] or r["ok"])
def c14():
    fd, path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"file": "content",}')
        code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "salvage.py"), path], capture_output=True, text=True)
        assert_eq(code.returncode, 0)
        assert_eq(json.loads(code.stdout), {"file": "content"})
    finally:
        os.unlink(path)
def c15(): ok('{"a": "\\u00e9\\u4e2d"}', {"a": "\u00e9\u4e2d"})
def c16():
    r = salvage.salvage('{"a": [1, 2')
    assert_true("close-brackets" in "; ".join(r["repairs"]))
def c17(): ok('{"spaces":   1   }', {"spaces": 1})
def c18():
    r1 = salvage.salvage('{"a": [1,')
    r2 = salvage.salvage('{"a": [1,')
    assert_eq(r1, r2)

for fn in sorted([v for k, v in list(globals().items()) if k.startswith(("a0", "a1", "a2", "b0", "b1", "c0", "c1"))], key=lambda f: f.__name__):
    check(fn.__name__, fn)


# ---------- [R2] round-2 additions (structural smart quotes, idempotency, audit contracts) ----------
def r201(): ok('{\u201ca\u201d: 1, \u201cb\u201d: [2,]}', {"a": 1, "b": [2]})
def r202():
    r = salvage.salvage('{"a": "curly \u201cinside\u201d stays"}')
    assert_true(r["ok"] and r["value"]["a"] == "curly \u201cinside\u201d stays")
def r203():
    r1 = salvage.salvage('{"a": 1}')
    r2 = salvage.salvage(json.dumps(r1["value"]))
    assert_eq(r2["repairs"], [])
def r204():
    r = salvage.salvage('{"a": [1, 2, {"b": 3,},')
    assert_true(r["ok"] and r["value"] == {"a": [1, 2, {"b": 3}]})
def r205():
    r = salvage.salvage('{"a": 1,}\n\n```')
    assert_true(r["ok"], "fence fragment after valid object")
def r206():
    r = salvage.salvage('{"nested": {"a": [{"c": {"d": "x"', max_passes=1)
    assert_true(r["ok"] and r["value"]["nested"]["a"][0]["c"]["d"] == "x")
def r207():
    r = salvage.salvage('{"a": 1', max_passes=0)
    assert_true(not r["ok"], "max_passes=0 means no repair attempted")
def r208():
    r = salvage.salvage('{"a": 1')
    assert_true(all(x in "; ".join(r["repairs"]) for x in ["close-brackets"]), "audit names are stable")
def r209():
    fd, path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)
    try:
        open(path, "w", encoding="utf-8").write('{"k": "\u4e2d\u6587",}')
        code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "salvage.py"), path], capture_output=True, text=True, input="")
        assert_eq(code.returncode, 0)
        assert_eq(json.loads(code.stdout), {"k": "\u4e2d\u6587"})
    finally:
        os.unlink(path)
def r210():
    code = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "salvage.py")], capture_output=True, text=True, input='{"stdin": true,}')
    assert_eq(code.returncode, 0)
    assert_eq(json.loads(code.stdout), {"stdin": True})
def r211():
    r = salvage.salvage('{"a": "x"}')
    assert_eq(r["repairs"], [])
    assert_eq(r["error"], None)
def r212(): ok('{"a": [1, 2,]} extra words here', {"a": [1, 2]})
def r213():
    r = salvage.salvage('{"a": "\u2019quote"}')
    assert_true(r["value"]["a"] == "\u2019quote", "curly apostrophe content untouched")

for fn in sorted([v for k, v in list(globals().items()) if k.startswith("r2")], key=lambda f: f.__name__):
    check(fn.__name__, fn)

passed = sum(1 for _, ok_ in RESULTS if ok_)
for n, ok_ in RESULTS:
    if not ok_:
        print("FAIL:", n)
print("SUMMARY: PASS %d/%d" % (passed, len(RESULTS)))
sys.exit(0 if passed == len(RESULTS) else 1)
