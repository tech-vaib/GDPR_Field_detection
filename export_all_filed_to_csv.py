import os
import json
import csv
from pymongo import MongoClient

# ===============================
# CONFIGURATION
# ===============================
MONGO_URI = "mongodb://username:password@host:port/?ssl=true&replicaSet=globaldb"  # Update
DATABASES = ["db1", "db2"]  # List of database names you want to export
OUTPUT_DIR = "dsar_exports"  # Directory to store CSVs
LIMIT = 10000  # Safety limit per collection

# ===============================
# Helper functions
# ===============================
def flatten_doc(doc, exclude_fields=None):
    """
    Flatten top-level fields; keep nested objects as JSON strings.
    exclude_fields: list of top-level fields to ignore (like _id)
    """
    if exclude_fields is None:
        exclude_fields = ["_id"]

    row = {}
    for k, v in doc.items():
        if k in exclude_fields:
            continue
        if isinstance(v, (dict, list)):
            row[k] = json.dumps(v, ensure_ascii=False)
        else:
            row[k] = v
    return row

def export_collection(db, collection_name, output_dir):
    collection = db[collection_name]
    cursor = collection.find({}, limit=LIMIT)

    # Discover top-level fields
    fields_set = set()
    sample_docs = []
    for doc in cursor:
        sample_docs.append(doc)
        fields_set.update(doc.keys())

    if not sample_docs:
        print(f"⚠️ No documents found in {collection_name}, skipping...")
        return

    # Exclude _id by default
    fields = [f for f in fields_set if f != "_id"]

    # Prepare CSV path
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, f"{collection_name}.csv")

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for doc in sample_docs:
            writer.writerow(flatten_doc(doc, exclude_fields=["_id"]))

    print(f"✅ Exported collection '{collection_name}' to {csv_path}")

# ===============================
# Main export function
# ===============================
def export_databases(mongo_uri, databases, output_dir):
    client = MongoClient(mongo_uri)
    for db_name in databases:
        print(f"\n🔹 Exporting database: {db_name}")
        db = client[db_name]
        collections = db.list_collection_names()
        print(f"Found collections: {collections}")

        for coll_name in collections:
            export_collection(db, coll_name, os.path.join(output_dir, db_name))

# ===============================
# Run export
# ===============================
if __name__ == "__main__":
    export_databases(MONGO_URI, DATABASES, OUTPUT_DIR)
