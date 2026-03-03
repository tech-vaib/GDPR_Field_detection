import csv
import json

def write_csv(filename, rows):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["id", "payload"])

        for row in rows:
            pretty_json = json.dumps(row["payload"], indent=4)
            pretty_json = pretty_json.replace("\n", "\r\n")
            writer.writerow([row["id"], pretty_json])
