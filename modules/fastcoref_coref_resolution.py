def get_replacements(d: dict) -> dict:
  replacements = list()
  # get a list of the intervals, their sizes, and replacements for each disambiguated referent cluster
  span_replacements = [(i, placeholder) for placeholder, intervals in d.items() for i in intervals]

  # sort the list of intervals by start and end
  span_replacements = sorted(span_replacements, key=lambda x: x[0])

  i = 0
  while i < len(span_replacements):
    # if the end of the list is reached
    if i + 1 == len(span_replacements):
        replacements.append(span_replacements[i])

    # if the next one DOESN'T have the same start position
    elif span_replacements[i][0][0] != span_replacements[i + 1][0][0]:
        replacements.append(span_replacements[i])

    # since span_replacements is sorted by start, end,
    #   (start1 == start2) ==> start2 will always be larger
    i += 1

  return replacements


def get_cluster_matches(text:str,
                     replacements: list,
                     model) -> dict:
  """
  returns a dict:
    keys correspond to the placeholder entities in the text
    values are lists of tuples
      tuple[0] = start index of the match in the original text
      tuple[1] = end index of the match in the original text
      tuple[2] = cluster text
  """

  # rebuild cluster dict
  cluster_labels = {c[1] for c in replacements}
  clusters = {c: list() for c in cluster_labels}

  for i, r in replacements:
    clusters[r].append((
      i[0],
      i[1],
      text[i[0]:i[1]]
    ))

  return clusters


def replace_clusters(text:str,
                     replacements: list,
                     model) -> str:

  new_text = list()
  s = 0
  for i, r in replacements:
    new_text.append(text[s:i[0]])
    new_text.append(r)
    s = i[1]

  new_text.append(text[s:])
  return "".join(new_text)


def resolve_text(text:str, coref_resolution_model) -> str:
  doc = coref_resolution_model(
    text,
    component_cfg={"fastcoref": {'resolve_text': True}}
  )

  return doc._.resolved_text


def get_clusters(text:str, fast_coref_model) -> dict:

  # get the coreference clusters
  preds = fast_coref_model.predict(texts=[text])
  all_clusters = preds[0].get_clusters(as_strings=False)

  # get disambiguated clusters
  return {f"E{i}": clusters for i, clusters in enumerate(all_clusters)}


def ambiguate_text(resolved_text: str,
                   nlp_model,
                   fast_coref_model) -> tuple:
  # restructure the clusters dict for replacement
  replacements = get_replacements(
    get_clusters(resolved_text, fast_coref_model)
  )

  # replace the cluster matches
  cluster_strings = get_cluster_matches(
    resolved_text,
    replacements,
    nlp_model
  )

  # ambiguate the text
  ambiguated_text = replace_clusters(
    resolved_text,
    replacements,
    nlp_model
  )

  return cluster_strings, ambiguated_text