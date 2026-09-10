# Repair Method v01

This candidate uses three fresh Astra calls under one trial deadline.

1. Inspect the factory. Retain a short report with observed facts, supply breaks, and possible repairs.
2. Repair the first supported break on each required supply chain. Retain the changes and current production evidence.
3. Check current production. Repair remaining clear faults and call `finish`.

The first stage has at most 65 seconds. The second has at most 145 seconds. The last stage uses the remaining time. Each model call uses the fixed subscription runner. The Method does not reset the deadline or action limit. A stage that ends without a full report passes that fact to the next stage, which must inspect the current state.

The prompts ask the model to use observed inserter endpoints, small repair batches, and fresh production counts. The final checker clears stored materials, so the policy must restore each supply chain.

This is a design choice, not a measured improvement. The candidate has not yet been scored.

Author access was limited to the public task, the initial Method bundle, the public Method runner interface, and approved development evidence. The author did not read case code, fixture code, reference code, case trees, final saves, or hidden controls. The only development result read before v01 was completed was the direct run summary and final report for `development-001`.
