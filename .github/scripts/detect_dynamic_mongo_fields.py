import ast
import sys
import json
from pathlib import Path

OUTPUT_FILE = "dynamic_mongo_findings.json"
FINDINGS = []


class MongoDynamicFieldVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename

    def report(self, node, message):
        FINDINGS.append(
            f"{self.filename}:{node.lineno} → {message}"
        )

    def visit_Subscript(self, node):
        # doc[field] = value
        if not isinstance(node.slice, ast.Constant):
            self.report(node, "Dynamic field assignment (doc[field])")
        self.generic_visit(node)

    def visit_Call(self, node):
        # dict.update(dynamic_dict)
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "update" and node.args:
                if not isinstance(node.args[0], ast.Dict):
                    self.report(node, "dict.update() with dynamic fields")

        # Mongo update operators using variables
        for arg in node.args:
            if isinstance(arg, ast.Dict):
                for key, value in zip(arg.keys, arg.values):
                    if isinstance(key, ast.Constant) and key.value in {
                        "$set", "$unset", "$push", "$addToSet", "$rename"
                    }:
                        if not isinstance(value, ast.Dict):
                            self.report(
                                node,
                                f"{key.value} uses dynamic field definitions"
                            )

        self.generic_visit(node)


def scan_file(file_path):
    try:
        source = Path(file_path).read_text()
        tree = ast.parse(source)
        MongoDynamicFieldVisitor(file_path).visit(tree)
    except (SyntaxError, UnicodeDecodeError):
        # Skip files we can't parse safely
        pass


if __name__ == "__main__":
    files = sys.argv[1:]

    for file in files:
        scan_file(file)

    if FINDINGS:
        with open(OUTPUT_FILE, "w") as f:
            json.dump(FINDINGS, f, indent=2)

        print("\n⚠️ Dynamic MongoDB Field Writes Detected:\n")
        for finding in FINDINGS:
            print(f" - {finding}")

        print(
            "\nAction required: Please explain what dynamic fields may be written "
            "and confirm GDPR / PII impact."
        )

        # ❌ Fail the build
        sys.exit(1)

    print("✅ No dynamic MongoDB field writes detected.")
    sys.exit(0)
