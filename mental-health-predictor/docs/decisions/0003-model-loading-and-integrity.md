# 0003. Load the model once at startup, verify its hash, refuse version mismatches

Status: accepted

## Context
The model is a pickled scikit-learn `Pipeline` (`Mental_Health_Model2.pkl`). Unpickling executes code
from the file, and pickles are tied to the scikit-learn version that wrote them.

## Decision
- Load once at startup (lifespan), not per request. A failure stops the app from starting.
- `MODEL_SHA256` is required when `APP_ENV=production`. The file's SHA-256 is checked before it is
  unpickled. In local and staging it is optional.
- scikit-learn's `InconsistentVersionWarning` is turned into a load error with a message naming both
  versions.
- After loading, the pipeline's `feature_names_in_` must equal the 12 columns the API maps to, and the
  one-hot encoder categories must exist for the 5 nominal columns. Dropdown options come from there.

## Alternatives considered
- Re-implement the model in a safe format (ONNX, JSON trees): removes both risks, but changes the
  artefact and needs its own validation. Possible later.
- Warn on version mismatch and continue: the failure mode is silently wrong predictions.

## Consequences
- Updating the model means updating `MODEL_SHA256` and, if needed, the pinned scikit-learn version.
- Cold start includes loading the file; health checks must not be wired to start before it is ready.
- This does not protect against someone who can change both the file and the environment variable.
