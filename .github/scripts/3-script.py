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

                # Detect collection name
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

                # Extract fields (for insert/update/replace)
                for arg in node.args:
                    if isinstance(arg, ast.Dict):
                        for k, v in zip(arg.keys, arg.values):
                            if isinstance(k, ast.Constant):

                                # Handle update operators
                                if isinstance(v, ast.Dict) and k.value in {
                                    "$set", "$unset", "$push",
                                    "$addToSet", "$rename",
                                    "$inc", "$pull"
                                }:
                                    for fk in v.keys:
                                        if isinstance(fk, ast.Constant):
                                            fields.add(str(fk.value))
                                        else:
                                            dynamic = True
                                else:
                                    fields.add(str(k.value))
                            else:
                                dynamic = True
                    else:
                        dynamic = True

                REPORT[op_type].append({
                    "file": self.filename,
                    "line": node.lineno,
                    "fields": sorted(fields),
                    "dynamic": dynamic,
                    "collection": coll_name
                })

        self.generic_visit(node)


def scan(file):
    try:
        tree = ast.parse(Path(file).read_text())
        MongoVisitor(file).visit(tree)
    except Exception:
        pass


if __name__ == "__main__":
    files = sys.argv[1:]

    for f in files:
        scan(f)

    # 🚫 If no Mongo writes detected → pass CI
    if not REPORT:
        print("✅ No MongoDB WRITE operations detected.")
        sys.exit(0)

    # 🛑 If detected → print report and fail CI
    print("## 🔍 MongoDB WRITE Operations Detected (GDPR Review Required)\n")

    if COLLECTIONS:
        print("### 📦 Collections Impacted")
        for c in sorted(COLLECTIONS):
            print(f"- {c}")
        print()

    for op, entries in REPORT.items():
        print(f"### {op}")
        for e in entries:
            severity = "⚠️ dynamic" if e['dynamic'] or e['collection'] == "<dynamic>" else "static"
            print(
                f"- {e['file']}:{e['line']} → "
                f"Collection: {e['collection']}, "
                f"Fields: {', '.join(e['fields']) if e['fields'] else '<none>'}, "
                f"{severity}"
            )
        print()

    # 🚨 Fail pipeline
    sys.exit(1)
