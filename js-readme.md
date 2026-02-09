(covers all real scenarios)
Use case covered

Top-level allow-list

Nested allow-lists

Arrays of primitives

Arrays of objects

Deep nesting

Controlled dynamic areas

Escape hatch for future

Safe rollout (warn → error)

WHAT THIS SCRIPT ALLOWS (ALL CASES)
Scenario	Allowed?	Why
Partial documents	✅	No required
Known top-level fields	✅	Allow-list
Unknown top-level fields	❌	additionalProperties: false
Nested objects	✅	Explicitly defined
Dynamic nested fields	✅	additionalProperties: true
Arrays of primitives	✅	items defined
Arrays of strict objects	✅	Controlled
Dynamic arrays	✅	Explicitly allowed
Future unknown fields	✅	extensions

SWITCH TO ENFORCEMENT MODE (WHEN READY)
db.runCommand({
  collMod: "customers",
  validationAction: "error"
})

Cosmos DB COMPATIBILITY
Platform	Behavior
MongoDB	✅ Fully enforced
Cosmos Mongo vCore	✅ Fully enforced
Cosmos Mongo RU	⚠️ Not reliable

-----------------
## To find what is enforced

db.getCollectionInfos().forEach(function (c) {
  print("Collection:", c.name);
  printjson(c.options.validator || "NO VALIDATOR");
});

## enforce:
db.runCommand({
  collMod: "customers",
  validationAction: "error"
});

## Initialize Schema Validation for All Collections
db.getCollectionNames().forEach(function (collName) {
  print("Applying baseline schema to collection:", collName);

  db.runCommand({
    collMod: collName,

    validator: {
      $jsonSchema: {
        bsonType: "object",

        // Allow ANY fields at top level
        additionalProperties: true
      }
    },

    // Safe rollout defaults
    validationLevel: "moderate",
    validationAction: "warn"
  });
});

## SCRIPT TO GATHER EXISTING FILED FOR COLLECTION

// ===============================
// CONFIG
// ===============================
const COLLECTION_NAME = "customers"; // 👈 change this

// ===============================
// Generate validator
// ===============================
const coll = db.getCollection(COLLECTION_NAME);
const fields = {};

coll.find({}, { _id: 0 }).forEach(doc => {
  Object.keys(doc).forEach(key => {
    fields[key] = true;
  });
});

const properties = {};
Object.keys(fields).forEach(field => {
  properties[field] = {
    description: "Auto-discovered existing field"
  };
});

const validator = {
  collection: COLLECTION_NAME,
  validator: {
    $jsonSchema: {
      bsonType: "object",
      properties: properties,
      additionalProperties: false
    }
  },
  validationLevel: "moderate",
  validationAction: "warn",
  generatedAt: new Date().toISOString()
};

// ===============================
// Print to console
// ===============================
print("✅ Validator for collection:", COLLECTION_NAME);
printjson(validator);
