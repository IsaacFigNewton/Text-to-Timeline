# Text-to-Timeline
### An general-purpose, ML/rule-based hybrid model for timeline reconstruction from natural language English text.
---

## Dependencies
- [FastCoref](https://pypi.org/project/fastcoref/)
  - Mainly used for coreference disambiguation
- [SpaCy](https://spacy.io)
  - Mainly used for dependency parsing
- [The FRED Api](http://wit.istc.cnr.it/stlab-tools/fred)
  - To try handling more complex time relations
---

## What this model does well
- Small and fast.
- Relatively few dependencies.
- Very interpretable.
- Good for getting a rough overview of the sequence of events in a doc
---

## What this model does poorly
- Not super accurate.
- Will occasionally miss connections during triplet extraction.
- Poor performance on long-range temporal associations.
- Infers event sequence based on ordering in text when unable to determine ordering from text itself.
