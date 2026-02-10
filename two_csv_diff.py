import csv

# ===============================
# CONFIGURATION
# ===============================
OLD_CSV = "mongo_columns_latest_with_id_previous.csv"  # previous CSV
NEW_CSV = "mongo_columns_latest_with_id.csv"           # latest CSV
OUTPUT_CSV = "column_diff_report.csv"

# ===============================
# Helper function
# ===============================
def read_columns(csv_file):
    """
    Read CSV with columns: collection, fields
    Returns a dict: {collection_name: set(fields)}
    """
    columns = {}
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            collection = row["collection"]
            fields = set(field.strip() for field in row["fields"].split(",") if field.strip())
            columns[collection] = fields
    return columns

# ===============================
# Compare columns
# ===============================
def compare_columns(old_csv, new_csv, output_csv):
    old_columns = read_columns(old_csv)
    new_columns = read_columns(new_csv)

    all_collections = set(old_columns.keys()).union(new_columns.keys())

    diffs = []

    for coll in sorted(all_collections):
        old_fields = old_columns.get(coll, set())
        new_fields = new_columns.get(coll, set())

        added = new_fields - old_fields
        removed = old_fields - new_fields

        if added or removed:
            diffs.append({
                "collection": coll,
                "added_fields": ", ".join(sorted(added)) if added else "",
                "removed_fields": ", ".join(sorted(removed)) if removed else ""
            })

    # Write diff CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["collection", "added_fields", "removed_fields"])
        writer.writeheader()
        for row in diffs:
            writer.writerow(row)

    print(f"✅ Column differences written to {output_csv}")

# ===============================
# Run comparison
# ===============================
if __name__ == "__main__":
    compare_columns(OLD_CSV, NEW_CSV, OUTPUT_CSV)
