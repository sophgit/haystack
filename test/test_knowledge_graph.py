from pathlib import Path

import pytest

from haystack.graph_retriever.text_to_sparql import Text2SparqlRetriever
from haystack.knowledge_graph.graphdb import GraphDBKnowledgeGraph


@pytest.mark.graph
def test_graph_retrieval(retriever_with_docs, document_store_with_docs):
    # doc_dir = "../data/tutorial10_knowledge_graph/"
    # s3_url = "https://fandom-qa.s3-eu-west-1.amazonaws.com/triples_and_config.zip"
    # fetch_archive_from_http(url=s3_url, output_dir=doc_dir)
    #
    # # Fetch a pre-trained BART model that translates natural language questions to SPARQL queries
    # doc_dir = "../saved_models/tutorial10_knowledge_graph/"
    # s3_url = "https://fandom-qa.s3-eu-west-1.amazonaws.com/saved_models/hp_v3.4.zip"
    # fetch_archive_from_http(url=s3_url, output_dir=doc_dir)

    # status = subprocess.run(
    #             ['docker run -d -p 7200:7200 --name graphdb-instance-tutorial docker-registry.ontotext.com/graphdb-free:9.4.1-adoptopenjdk11'], shell=True
    #         )

    kg = GraphDBKnowledgeGraph(index="tutorial_10_index")
    kg.create_index(config_path=Path("../data/tutorial10_knowledge_graph/repo-config.ttl"))
    kg.import_from_ttl_file(index="tutorial_10_index",
                            path=Path("../data/tutorial10_knowledge_graph/triples.ttl"))
    triple = {'p': {'type': 'uri', 'value': 'https://deepset.ai/harry_potter/_paternalgrandfather'}, 's': {'type': 'uri', 'value': 'https://deepset.ai/harry_potter/Melody_fawley'}, 'o': {'type': 'uri', 'value': 'https://deepset.ai/harry_potter/Marshall_fawley'}}
    triples = kg.get_all_triples()
    assert len(triples) > 0
    assert triple in triples

    # Define prefixes for names of resources so that we can use shorter resource names in queries
    prefixes = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX hp: <https://deepset.ai/harry_potter/>
    """
    kg.prefixes = prefixes

    kgqa_retriever = Text2SparqlRetriever(knowledge_graph=kg,
                                          model_name_or_path="../saved_models/tutorial10_knowledge_graph/hp_v3.4")

    question_text = "In which house is Harry Potter?"
    result = kgqa_retriever.retrieve(question_text=question_text)
    assert result[0] == {'answer': ['https://deepset.ai/harry_potter/Gryffindor'], 'meta': {'model': 'Text2SparqlRetriever', 'sparql_query': 'select ?a { hp:Harry_potter hp:house ?a . }'}}

    result = kgqa_retriever._query_kg(query="select distinct ?sbj where { ?sbj hp:job hp:Keeper_of_keys_and_grounds . }")
    assert result[0][0] == "https://deepset.ai/harry_potter/Rubeus_hagrid"

    result = kgqa_retriever._query_kg(
        query="select distinct ?obj where { <https://deepset.ai/harry_potter/Hermione_granger> <https://deepset.ai/harry_potter/patronus> ?obj . }")
    assert result[0][0] == "https://deepset.ai/harry_potter/Otter"