from spacy.matcher import Matcher
import pyinflect
import spacy
from spacy.tokens import Doc, Token


def simplify_made_it(doc, matcher):
    matches = matcher(doc)
    # Sort so inner spans get merged first
    matches = sorted(matches, key=lambda m: (m[1], -m[2]))
    with doc.retokenize() as retok:
        for match_id, start, end in matches:
            span = doc[start:end]             # e.g. ["made","it","clear"]
            target = span[2]                  # the X token
            # Try inflecting to past participle (VBN)
            new_form = target._.inflect("VBN")
            if not new_form:
                # fall back to lemma + "ed" if inflection fails
                new_form = target.lemma_ + "ed"
            # Merge span into one token with updated morphology
            attrs = {
                "ORTH": new_form,
                "LEMMA": target.lemma_,
                "POS": "VERB",
                "TAG": "VBN"
            }
            retok.merge(span, attrs=attrs)
    return doc