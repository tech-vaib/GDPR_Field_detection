import ast
import sys
from pathlib import Path
from collections import defaultdict

REPORT = defaultdict(list)
COLLECTIONS = set()

# MongoDB CRUD method mapping
MONGO_WRITE_METHODS = {
    "insert_one": "INSERT",
    "insert_many": "INSERT",
    "replace_one": "INSERT/REPLACE",
    "update_one": "UPDATE",
    "update_many": "UPDATE",
    "delete_one": "DELETE",
    "delete_many": "DELETE",
}


class MongoVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr

            if method in MONGO_WRITE_METHODS:
                op_type = MONGO_WRITE_METHODS[method]
                fields = set()
                dynamic = False

                # Detect collection name (best effort)
                coll_name = "<unknown>"
                if isinstance(node.func.value, ast.Attribute):
                    coll_name = node.func.value.attr
                elif isinstance(node.func.value, ast.Subscript):
                    if isinstance(node.func.value.slice, ast.Constant):
                        coll_name = str(node.func.value.slice.value)
                    else:
                        coll_name = "<dynamic>"
                COLLECTIONS.add(coll_name)

                # Scan arguments
                for arg in node.args:
                    if isinstance(arg, ast.Dict):
                        for k, v in zip(arg.keys, arg.values):
                            if isinstance(k, ast.Constant):
                                # Check for Mongo operators
                                if isinstance(v, ast.Dict) and k.value in {
                                    "$set", "$unset", "$push", "$addToSet", "$rename"
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
        # Skip unparseable files
        pass


if __name__ == "__main__":
    files = sys.argv[1:]
    for f in files:
        scan(f)

    if not REPORT and not COLLECTIONS:
        sys.exit(0)

    # Generate PR comment report
    with open("mongo_crud_report.md", "w") as f:
        f.write("## 🔍 MongoDB CRUD Activity Detected (Manual GDPR Review Required)\n\n")

        if COLLECTIONS:
            f.write("### 📦 Collections Used\n")
            for c in sorted(COLLECTIONS):
                f.write(f"- `{c}`\n")
            f.write("\n")

        for op, entries in REPORT.items():
            f.write(f"### {op}\n")
            for e in entries:
                f.write(
                    f"- `{e['file']}:{e['line']}` → "
                    f"Collection: `{e['collection']}`, "
                    f"Fields: {', '.join(e['fields']) if e['fields'] else '<none>'}"
                    f"{' ⚠️ dynamic' if e['dynamic'] else ''}\n"
                )
            f.write("\n")

    # ❌ Block merge if any CRUD activity detected
    sys.exit(1)
