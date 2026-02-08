# MongoDB CRUD GDPR CI Check

This GitHub Actions workflow automatically scans Python code in pull requests
for **MongoDB CRUD operations** and surfaces them for **manual GDPR / PII review**.

It supports Cosmos DB Mongo (RU & vCore) and standard MongoDB.

---

## Features

- Detects **all MongoDB CRUD operations**:
  - `insert_one`, `insert_many`, `replace_one`
  - `update_one`, `update_many`
  - `delete_one`, `delete_many`
- Detects **both static and dynamic fields**
- Detects **collection usage**:
  - Static collections (e.g., `db.customer`)
  - Dynamic collections (e.g., `db[get_collection_name()]`)
- Generates **PR comments** with:
  - File names and line numbers
  - Collection names
  - Fields involved
  - Dynamic flags for unclear fields/collections
- Assigns **severity levels**:
  - ✅ `static` — Fields and collections are literals
  - ⚠️ `dynamic` — Field or collection is dynamic / unknown
- Automatically adds **GitHub PR labels**:
  - `mongo-dynamic` — Dynamic fields detected
  - `mongo-dynamic-collection` — Dynamic collection detected
- **Blocks merge** if any Mongo CRUD activity is detected
- Scans **only changed Python files** in PRs

---

## What is covered

- Any **changed Python files** in a PR
- Static field inserts and updates
- Dynamic field inserts and updates
- CRUD calls to new or existing collections (static or dynamic)
- CRUD operations anywhere in the Python AST (direct calls)
- `$set`, `$unset`, `$push`, `$addToSet`, `$rename` operators

---

## What is NOT fully covered

- Collection names generated entirely at runtime and passed from external sources
- Document objects built far away from the CRUD call
- Writes via external libraries or ORMs
- Mongo operations outside Python code (shell scripts, Spark, Admin console)

> Mitigation: flagged lines in PR comments require **manual GDPR review**.

---

## How it works

1. Workflow triggers on PR **open**, **synchronize**, or **reopen**
2. Checks **only changed Python files**
3. Python AST script detects:
   - CRUD operation type
   - Collection name
   - Field names
   - Dynamic flags
4. Generates a **Markdown report** and posts as a **PR comment**
5. Workflow assigns **PR labels** based on severity:
   - Dynamic fields → `mongo-dynamic`
   - Dynamic collections → `mongo-dynamic-collection`
6. Workflow **fails the PR** to block merge until review

---

## Severity Levels & PR Labels

| Severity | Meaning | GitHub Label |
|----------|--------|--------------|
| ✅ static | Field names and collection names are literals | none |
| ⚠️ dynamic | Field or collection name is dynamic or unknown | `mongo-dynamic` / `mongo-dynamic-collection` |

> Reviewers should focus first on dynamic operations, which pose higher GDPR / PII risk.

---

## Example PR Comment

MongoDB CRUD Activity Detected (Manual GDPR Review Required)
📦 Collections Used

customer

orders

<dynamic>
INSERT

services/customer_repo.py:34 → Collection: customer, Fields: email, name ✅ static

services/order_repo.py:19 → Collection: <dynamic>, Fields: status ⚠️ dynamic

UPDATE

services/customer_repo.py:78 → Collection: customer, Fields: phone ✅ static

DELETE

services/customer_repo.py:102 → Collection: customer, Fields: email ✅ static
