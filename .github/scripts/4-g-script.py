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
        self.variables = {}

    def visit_Assign(self, node):
        # Track: collection = db.users
        if isinstance(node.value, ast.Attribute):
            if isinstance(node.value.value, ast.Name):
                coll = node.value.attr
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.variables[target.id] = coll

        # Track: collection = db["users"]
        if isinstance(node.value, ast.Subscript):
            if isinstance(node.value.slice, ast.Constant):
                coll = str(node.value.slice.value)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.variables[target.id] = coll

        self.generic_visit(node)

    def resolve_collection(self, node):
        # db.users
        if isinstance(node, ast.Attribute):
            return node.attr

        # db["users"]
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Constant):
                return str(node.slice.value)

        # variable
        if isinstance(node, ast.Name):
            return self.variables.get(node.id, "<unknown>")

        return "<unknown>"

    def extract_fields(self, node):
        fields = set()
        dynamic = False

        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant):
                    key = str(k.value)

                    # Handle Mongo operators like $set
                    if isinstance(v, ast.Dict) and key.startswith("$"):
                        for fk in v.keys:
                            if isinstance(fk, ast.Constant):
                                fields.add(str(fk.value))
                            else:
                                dynamic = True
                    else:
                        fields.add(key)
                else:
                    dynamic = True
        else:
            dynamic = True

        return fields, dynamic

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr

            if method in MONGO_METHODS:
                op_type = MONGO_METHODS[method]

                coll_name = self.resolve_collection(node.func.value)
                COLLECTIONS.add(coll_name)

                fields = set()
                dynamic = False

                for arg in node.args:
                    f, d = self.extract_fields(arg)
                    fields.update(f)
                    dynamic = dynamic or d

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
        content = Path(file).read_text()
        tree = ast.parse(content)
        MongoVisitor(file).visit(tree)
    except Exception as e:
        print(f"⚠️ Failed to parse {file}: {e}")


if __name__ == "__main__":
    files = sys.argv[1:]

    for f in files:
        scan(f)

    if not REPORT:
        print("✅ No MongoDB WRITE operations detected.")
        sys.exit(0)

    print("## 🔍 MongoDB WRITE Operations Detected (GDPR Review Required)\n")

    if COLLECTIONS:
        print("### 📦 Collections Impacted")
        for c in sorted(COLLECTIONS):
            print(f"- {c}")
        print()

    for op, entries in REPORT.items():
        print(f"### {op}")
        for e in entries:
            severity = "⚠️ dynamic" if e['dynamic'] or e['collection'] == "<unknown>" else "static"
            print(
                f"- {e['file']}:{e['line']} → "
                f"Collection: {e['collection']}, "
                f"Fields: {', '.join(e['fields']) if e['fields'] else '<none>'}, "
                f"{severity}"
            )
        print()

    sys.exit(1)
