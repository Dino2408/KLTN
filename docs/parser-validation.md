# Parser Validation

A generated parser is evaluated against a sample set before activation.

Minimum validation dimensions:
- parse success rate
- required-field extraction
- type correctness
- false extraction rate
- preservation of the raw event
- deterministic replay

The registry should record parser version, source fingerprint, sample count, validation metrics and approval state.

Recommended lifecycle:
candidate -> testing -> validated -> active -> superseded/rejected.
