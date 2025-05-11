import json
import spacy
from fastcoref import FCoref, spacy_component
from pipeline import *
from utils import *


def run_tests(texts:list, model, coref_resolution_model):
  ambiguated_texts = [[t, None] for t in texts]
  ambiguated_test = None

  for i in range(len(texts)):
    _, ambiguated_test = ambiguate_text(texts[i],
                                        nlp_model=model,
                                        fast_coref_model=fastcoref_model,
                                        coref_resolution_model=coref_resolution_model)
    # get the coreference clusters
    ambiguated_texts[i][1] = ambiguated_test

  for test in ambiguated_texts:
    print(f"original:\n{test[0]}")
    print(f"disambiguated:\n{test[1]}")
    # print()

if __name__ == "__main__":
    default_nlp_model = spacy.load("en_core_web_sm")

    fastcoref_model = FCoref()

    coref_resolution_model = spacy.load("en_core_web_sm", exclude=["parser", "lemmatizer", "ner", "textcat"])
    coref_resolution_model.add_pipe("fastcoref")

    tests = [
        "The frog jumped over the goose. Mr. Holmes is gay. Then the frog fell into the abyss. The goose followed the frog into the abyss and after that ate a different frog.",
        "Although he was very busy with his work, Peter had had enough of it. He and his wife decided they needed a holiday. They travelled to Spain because they loved the country very much.",
        "John met Paul after he finished work. He suggested they grab a drink.",
        "The book was on the table when Sarah handed it to Mary. She smiled and thanked her.",
        "Tom told Jerry that he had failed the exam.",
        "The city council refused the demonstrators a permit because they feared violence.",
        "Anna told Lucy that her idea was brilliant.",
        "The scientist interviewed the assistant while she was setting up the experiment.",
        "After the dog bit the man, he ran away.",
        "The mechanic fixed the car while it was raining. He was soaked by the end.",
        "David thanked Michael after his birthday party.",
        "Karen lent her book to Julie because she needed it for class."
    ]
    run_tests(tests,
              default_nlp_model,
              coref_resolution_model)
    print("\n\n")

    test_0 = get_text_info_json(tests[0],
                                nlp_model=default_nlp_model,
                                fastcoref_model=fastcoref_model,
                                coref_resolution_model=coref_resolution_model)
    print(json.dumps(test_0, indent=4, default=str))
    print("\n\n")

    plot_graph_from_edge_list(test_0["edges"])
    print("\n\n")