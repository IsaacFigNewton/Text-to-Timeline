# Text-to-Timeline
### An general-purpose, ML/rule-based hybrid model for timeline reconstruction from natural language English text.
---

## Dependencies
### Required
- [FastCoref](https://pypi.org/project/fastcoref/)
  - Mainly used for coreference disambiguation
- [SpaCy](https://spacy.io)
  - Mainly used for dependency parsing
- [IntervalTree](https://pypi.org/project/intervaltree/)
  - Coming soon

### Optional
- [rdflib](https://rdflib.readthedocs.io/en/stable/)
  - Coming soon
- [flufl.enum](https://pypi.org/project/flufl.enum/)
  - Coming soon
- [The FRED Api](http://wit.istc.cnr.it/stlab-tools/fred)
  - To try handling more complex time relations
  - Coming soon
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
---

# Getting Started
## Usage with Google Colab
### 1. Add the following cells to your notebook
#### Package Downloads
```python
# for fastcoref
!pip install fastcoref

# for IntervalTree - coming soon
!pip install intervaltree

# for FRED - coming soon
!wget https://raw.githubusercontent.com/IsaacFigNewton/fredlib-updated/refs/heads/main/fredlib.py
!pip install rdflib flufl.enum
```
#### Environment variable setup (optional)
```python
from google.colab import userdata
# You'll need an API key if you want to include FRED
fred_api_key = userdata.get("fred_api")
```

### 2. Copy and paste the code from `tests.py` into the cells of your notebook
### 3. Run your notebook
---

## Library usage
### 1. Run the following commands to install the dependencies for spacy, matplotlib, fastcoref, etc. if they're not on your machine already:
```shell
pip install matplotlib

pip install spacy
python -m spacy download en_core_web_sm
# you may have to run the following command if you're getting an error from spacy
# python -m spacy download en

pip install fastcoref

# for IntervalTree - coming soon
pip install intervaltree

# for FRED (optional) - coming soon
wget https://raw.githubusercontent.com/IsaacFigNewton/fredlib-updated/refs/heads/main/fredlib.py
pip install rdflib flufl.enum
```
2. Run `tests.py`
