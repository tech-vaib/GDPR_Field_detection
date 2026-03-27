import ast
import sys
from pathlib import Path
from collections import defaultdict

REPORT = defaultdict(list)
COLLECTIONS = set()

MONGO_METHODS = {
    "insert_one": "INSERT",
    "insert_many": "INSERT",
    "replace_one": "REPLACE",
    "update_one": "UPDATE",
    "update_many": "UPDATE",
    "delete_one": "DELETE",
    "delete_many": "DELETE",
    "create_collection": "CREATE_COLLECTION",
}

# Ops where the first positional arg is a filter (not a write payload)
FILTER_FIRST_OPS = {"UPDATE", "REPLACE"}

UPDATE_OPERATORS = {
    "$set", "$unset", "$push",
    "$addToSet", "$rename",
    "$inc", "$pull"
}


def extract_fields_from_dict(dict_node, fields, dynamic_flag):
    """
    Walk an ast.Dict and extract written field names.
    Returns updated dynamic_flag (True if any dynamic key was found).
    """
    for k, v in zip(dict_node.keys, dict_node.values):
        if isinstance(k, ast.Constant):
            # Handle update operators like $set, $push, etc.
            if isinstance(v, ast.Dict) and k.value in UPDATE_OPERATORS:
                for fk in v.keys:
                    if isinstance(fk, ast.Constant):
                        fields.add(str(fk.value))
                    else:
                        dynamic_flag = True
            else:
                fields.add(str(k.value))
        else:
            dynamic_flag = True
    return dynamic_flag


class MongoVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr

            if method in MONGO_METHODS:
                op_type = MONGO_METHODS[method]
                fields = set()
                dynamic = False
                coll_name = "<unknown>"

                # --- Detect collection name ---
                if method == "create_collection":
                    if node.args and isinstance(node.args[0], ast.Constant):
                        coll_name = str(node.args[0].value)
                    else:
                        coll_name = "<dynamic>"
                else:
                    if isinstance(node.func.value, ast.Attribute):
                        coll_name = node.func.value.attr
                    elif isinstance(node.func.value, ast.Subscript):
                        if isinstance(node.func.value.slice, ast.Constant):
                            coll_name = str(node.func.value.slice.value)
                        else:
                            coll_name = "<dynamic>"

                COLLECTIONS.add(coll_name)

                # --- Extract fields from positional args ---
                # FIX (Bug 2 & 4): For UPDATE/REPLACE, skip the first positional arg
                # because it is the *filter* dict, not the write payload.
                write_args = node.args[1:] if op_type in FILTER_FIRST_OPS else node.args

                for arg in write_args:
                    if isinstance(arg, ast.Dict):
                        dynamic = extract_fields_from_dict(arg, fields, dynamic)
                    else:
                        # Non-dict positional arg → payload is dynamic (variable, call, etc.)
                        dynamic = True

                # --- FIX (Bug 3): Also inspect keyword arguments ---
                for kw in node.keywords:
                    if isinstance(kw.value, ast.Dict):
                        dynamic = extract_fields_from_dict(kw.value, fields, dynamic)

                REPORT[op_type].append({
                    "file": self.filename,
                    "line": node.lineno,
                    "fields": sorted(fields),
                    "dynamic": dynamic,
                    "collection": coll_name
                })

        self.generic_visit(node)


def scan(file):
    # FIX (Bug 1): Surface errors instead of silently swallowing them
    try:
        tree = ast.parse(Path(file).read_text(encoding="utf-8"))
        MongoVisitor(file).visit(tree)
    except Exception as e:
        print(f"⚠️  Could not scan {file}: {e}", file=sys.stderr)


if __name__ == "__main__":
    files = sys.argv[1:]

    if not files:
        print("Usage: mongo_crud_detector.py <file1.py> [file2.py ...]", file=sys.stderr)
        sys.exit(0)

    for f in files:
        scan(f)

    # No Mongo writes detected → pass CI
    if not REPORT:
        print("✅ No MongoDB WRITE operations detected.")
        sys.exit(0)

    # Writes detected → print report and fail CI
    print("## 🔍 MongoDB WRITE Operations Detected (GDPR Review Required)\n")

    if COLLECTIONS:
        print("### 📦 Collections Impacted")
        for c in sorted(COLLECTIONS):
            print(f"- {c}")
        print()

    for op, entries in REPORT.items():
        print(f"### {op}")
        for e in entries:
            severity = "⚠️  dynamic" if e["dynamic"] or e["collection"] == "<dynamic>" else "static"
            print(
                f"- {e['file']}:{e['line']} → "
                f"Collection: {e['collection']}, "
                f"Fields: {', '.join(e['fields']) if e['fields'] else '<none>'}, "
                f"{severity}"
            )
        print()

    # Fail pipeline
    sys.exit(1)
