# VIGILANT Evaluation Protocol

## Research questions

1. How accurately does VIGILANT recover requirement-to-code and
   requirement-to-test links?
2. Does graph and change evidence improve affected-artifact identification?
3. Do consistency rules identify broken traceability without fabricating
   evidence?
4. What is the contribution of retrieval, graph traversal, and agent
   orchestration in ablation runs?

## Required splits

- Split by repository or project version, never by randomly mixing artifacts
  from the same change across train and test.
- For temporal analysis, use an earlier commit for analysis and a later commit
  for evaluation.
- Keep gold links separate from retrieved evidence and generated explanations.

## Metrics

- Link recovery: Precision@K, Recall@K, F1, MAP, and MRR.
- Change impact: direct-change precision/recall and affected-artifact recall.
- Consistency: finding precision, finding recall, severity-weighted F1, and
  uncertain-rate.
- Evidence quality: percentage of findings with source path, location, and
  supporting artifact IDs.
- Operational: runtime, artifact count, memory, and optional model/API cost.

## Baselines and ablations

1. Lexical retrieval only.
2. Lexical retrieval plus structural/API/test signals.
3. Retrieval plus graph traversal.
4. Retrieval plus graph plus change evidence.
5. Full bounded investigator.

Every result must include repository revision, configuration, thresholds,
dependency versions, dataset catalog row, and output path. Poor results are
recorded as observed; no labels or metrics are synthesized.
