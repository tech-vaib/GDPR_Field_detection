// ===============================
// CONFIG
// ===============================
const COLLECTION_NAME = "customers";

// ===============================
// Extract top-level fields via aggregation
// ===============================
const pipeline = [
  { $limit: 10000 }, // safety cap
  {
    $project: {
      keys: {
        $objectToArray: "$$ROOT"
      }
    }
  },
  { $unwind: "$keys" },
  {
    $group: {
      _id: null,
      fields: { $addToSet: "$keys.k" }
    }
  }
];

const result = db.getCollection(COLLECTION_NAME).aggregate(pipeline).toArray();

if (result.length === 0) {
  print(`⚠️ No documents found or no fields extracted for ${COLLECTION_NAME}`);
} else {
  const properties = {};
  result[0].fields.forEach(field => {
    if (field !== "_id") {
      properties[field] = {
        description: "Auto-discovered existing field"
      };
    }
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
    validationAction: "warn"
  };

  print("✅ Generated validator:");
  printjson(validator);
}
