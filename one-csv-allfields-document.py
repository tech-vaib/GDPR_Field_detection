import csv
from pymongo import MongoClient

# ===============================
# CONFIGURATION
# ===============================
MONGO_URI = "mongodb://username:password@host:port/?ssl=true&replicaSet=globaldb"  # Update
DATABASES = ["db1", "db2"]  # List of databases
OUTPUT_FILE = "mongo_columns_latest_with_id.csv"

# ===============================
# Helper function
# ===============================
def get_latest_fields(collection):
    """
    Return top-level fields from the latest document in the collection, including _id.
    """
    latest_doc = collection.find_one(sort=[("_id", -1)])
    if not latest_doc:
        return set()
    # Include _id now
    return set(latest_doc.keys())

# ===============================
# Main function
# ===============================
def extract_latest_columns(mongo_uri, databases, output_file):
    client = MongoClient(mongo_uri)
    all_rows = []

    for db_name in databases:
        db = client[db_name]
        collections = db.list_collection_names()

        for coll_name in collections:
            collection = db[coll_name]
            fields_set = get_latest_fields(collection)

            all_rows.append({
                "collection": f"{db_name}.{coll_name}",
                "fields": ", ".join(sorted(fields_set))
            })

    # Write CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["collection", "fields"])
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

    print(f"✅ Latest columns including _id extracted to {output_file}")

# ===============================
# Run script
# ===============================
if __name__ == "__main__":
    extract_latest_columns(MONGO_URI, DATABASES, OUTPUT_FILE)
