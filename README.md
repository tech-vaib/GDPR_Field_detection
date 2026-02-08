# MongoDB CRUD GDPR CI Check

This GitHub Actions workflow automatically scans Python code in pull requests
for **MongoDB CRUD operations** and surfaces them for **manual GDPR / PII review**.

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
- **Blocks merge** if any Mongo CRUD operation is detected
- Works for **Cosmos DB Mongo (RU & vCore)** and regular MongoDB

---

## What is covered

- Any **changed Python files** in a PR
- Static field inserts and updates
- Dynamic field inserts and updates
- New collections used in PR (if literal or dynamic)
- CRUD operations anywhere in the Python AST (direct calls)

---

## What is NOT fully covered

- Collection names generated entirely at runtime and passed from elsewhere
- Document objects built far from the CRUD call
- Writes via external libraries or ORMs
- Mongo operations outside Python code (shell scripts, Spark, etc.)

> Mitigation: reviewers must manually inspect flagged lines for GDPR impact.

---

## How it works

1. Workflow triggers on PR open, synchronize, or reopen
2. Checks **only changed Python files**
3. Python AST script detects:
   - CRUD operation type
   - Collection name
   - Field names
   - Dynamic flags
4. Generates a **Markdown report** and posts as a **PR comment**
5. Workflow fails the PR, **blocking merge** until reviewed

---

## Example PR Comment

MongoDB CRUD Activity Detected (Manual GDPR Review Required)
📦 Collections Used

customer

orders

<dynamic>
INSERT

services/customer_repo.py:34 → Collection: customer, Fields: email, name

services/order_repo.py:19 → Collection: <dynamic>, Fields: status ⚠️ dynamic

UPDATE

services/customer_repo.py:78 → Collection: customer, Fields: phone

DELETE

services/customer_repo.py:102 → Collection: customer, Fields: email


---

## GDPR / PII Compliance

- Flags all Mongo CRUD activity for **manual review**
- Ensures **no data write goes unnoticed**
- Maintains **audit trail via PR comments**
- Covers **most common Python Mongo usage patterns**

