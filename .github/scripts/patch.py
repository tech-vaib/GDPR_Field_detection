def extract_added_lines_from_patch(patch_file):
    from collections import defaultdict

    file_changes = defaultdict(list)
    current_file = None

    with open(patch_file, "r") as f:
        for line in f:
            # Track file name
            if line.startswith("+++ b/"):
                current_file = line.strip().replace("+++ b/", "")
                continue

            # Capture only added lines (ignore +++)
            if line.startswith("+") and not line.startswith("+++"):
                if current_file:
                    file_changes[current_file].append(line[1:])  # strip '+'

    return file_changes

def scan_diff(file, lines):
    try:
        code = "".join(lines)

        if not code.strip():
            return

        tree = ast.parse(code)
        MongoVisitor(file).visit(tree)

    except Exception:
        # Ignore invalid partial snippets
        pass

  #add 
  patch_file = sys.argv[1]

file_changes = extract_added_lines_from_patch(patch_file)

for file, lines in file_changes.items():
    scan_diff(file, lines)


## add in workflow

- name: Generate diff patch (added lines only)
  run: |
    BASE=$(git merge-base ${{ github.event.pull_request.base.sha }} ${{ github.sha }})
    git diff -U0 $BASE ${{ github.sha }} -- '*.py' > diff.patch


- name: Run Mongo CRUD detector
  id: detector
  run: |
    set +e

    python .github/scripts/mongo_crud_detector.py diff.patch > report.txt
    exit_code=$?

    cat report.txt

    echo "report<<EOF" >> $GITHUB_OUTPUT
    cat report.txt >> $GITHUB_OUTPUT
    echo "EOF" >> $GITHUB_OUTPUT

    echo "exit_code=$exit_code" >> $GITHUB_OUTPUT


if: always()
