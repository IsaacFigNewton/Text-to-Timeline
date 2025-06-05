import json
import spacy
from spacy.matcher import Matcher
from fastcoref import FCoref, spacy_component

from .pipeline import *
from .clean_rdf_graph import *
from .timeline_construction import get_timeline


if __name__ == "__main__":
    default_nlp_model = spacy.load("en_core_web_sm")
    fastcoref_model = FCoref()
    coref_resolution_model = spacy.load(
        "en_core_web_sm",
        exclude=["parser", "lemmatizer", "ner", "textcat"]
    )
    coref_resolution_model.add_pipe("fastcoref")
    
    
    # Set up a Matcher for [made][it][ADJ]
    matcher = Matcher(default_nlp_model.vocab)
    pattern = [
        {"LEMMA": "make", "POS": "VERB"},
        {"LOWER": "it"},
        {"POS": {"IN": ["ADJ", "VERB", "NOUN"]}},  # adjectives, participles, or even nouns
    ]
    matcher.add("MAKE_IT_PATTERN", [pattern])
    

    tests = [
        # "He made it clear that she disagreed."
        # "He bought her the book. She said that he was lying. I believe she understands the issue. He made it clear that he disagreed. They assumed the problem was solved.",
        "The frog jumped over the goose. Mr. Holmes is gay. Then the frog fell into the abyss. The goose followed the frog into the abyss and after that ate a different frog.",
        # "Although he was very busy with his work, Peter had had enough of it. He and his wife decided they needed a holiday. They travelled to Spain because they loved the country very much.",
        # "John met Paul after he finished work. He suggested they grab a drink.",
        # "The book was on the table when Sarah handed it to Mary. She smiled and thanked her.",
        # "Tom told Jerry that he had failed the exam.",
        # "The city council refused the demonstrators a permit because they feared violence.",
        # "Anna told Lucy that her idea was brilliant.",
        # "The scientist interviewed the assistant while she was setting up the experiment.",
        # "After the dog bit the man, he ran away.",
        # "The mechanic fixed the car while it was raining. He was soaked by the end.",
        # "David thanked Michael after his birthday party.",
        # "Karen lent her book to Julie because she needed it for class."
    ]
    # run_tests(tests,
    #           default_nlp_model,
    #           fastcoref_model)
    # print("\n\n")


    with open('./maps/tags.json', 'r', encoding='utf-8') as f:
        all_tags = json.load(f)
    rel_pos_tags = all_tags["rel_pos_tags"]
    with open('./maps/temporal_relations/allen_intervals.json', 'r', encoding='utf-8') as f:
        temporal_relations_map = json.load(f)
    temporal_relations_map = {k: (v.get("start"), v.get("end")) for k, v in temporal_relations_map.items()}
    with open('./maps/temporal_relations/predicate_map.json', 'r', encoding='utf-8') as f:
        TEMPORAL_PREDICATE_MAP = json.load(f)
    file_prefix = "test_"
    rdf_temp_prefix = "boxer.owl: temp_"

    test_0 = get_text_info(
        tests[0],
        default_nlp_model,
        fastcoref_model,
        coref_resolution_model,
        matcher
    )
    print(json.dumps(test_0, indent=4, default=str))
    print("\n\n")

    plot_graph_from_edge_list(
        test_0["edges"],
        k=400,
        shape=(10, 10)
    )
    print("\n\n")

    # # get all temporal relations in order
    # #   TODO: INTEGRATE WITH EVENT TRIPLE PARSER
    # temp_relations = [[e[0], e[2]["labels"], e[1]]
    #                   for e in G0.edges(data=True)
    #                   if "temp_" in e[2]["labels"]]
    # timeline = get_timeline(
    #     event_seq=temp_relations,
    #     rel_pos_tags=rel_pos_tags,
    #     temporal_relations_map=temporal_relations_map,
    #     prefix=rdf_temp_prefix
    # )

    # plot_interval_tree(timeline, grid=False)