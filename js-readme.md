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
