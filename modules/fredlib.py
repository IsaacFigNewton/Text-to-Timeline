import os
import sys
import json
import rdflib
from flufl.enum import Enum
from rdflib import plugin
from rdflib.serializer import Serializer
# from rdflib.plugins.memory import IOMemory

__author__ = 'Misael Mongiovi, Andrea Giovanni Nuzzolese'

plugin.register('application/rdf+xml', Serializer, 'rdflib.plugins.serializers.rdfxml', 'XMLSerializer')
plugin.register('xml', Serializer, 'rdflib.plugins.serializers.rdfxml', 'XMLSerializer')

valid_json_types = {str, int, float, bool, None}

class FredType(Enum):
    Situation = 1
    Event = 2
    NamedEntity = 3
    SkolemizedEntity = 4
    Quality = 5
    Concept = 6

class NodeType(Enum):
    Class = 1
    Instance = 0

class ResourceType(Enum):
    Fred = 0
    Dbpedia = 1
    Verbnet = 2

class EdgeMotif(Enum):
    Identity = 1
    Type = 2
    SubClass = 3
    Equivalence = 4
    Role = 5
    Modality = 6
    Negation = 7
    Property = 8

class NaryMotif(Enum):
    Event = 1
    Situation = 2
    OtherEvent = 3
    Concept = 4

class PathMotif(Enum):
    Type = 1
    SubClass = 2

class ClusterMotif(Enum):
    Identity = 1
    Equivalence = 2
    IdentityEquivalence = 3 #all concepts tied by a sequence of sameAs and equivalentClass in any direction

class Role(Enum):
    Agent = 1
    Patient = 2
    Theme = 3
    Location = 4
    Time = 5
    Involve = 6
    Declared = 7
    VNOblique = 8
    LocOblique = 9
    ConjOblique = 10
    Extended = 11
    Associated = 12

class FredNode(object):
    def __init__(self,nodetype,fredtype,resourcetype):
        self.Type = nodetype
        self.FredType = fredtype
        self.ResourceType = resourcetype

class FredEdge(object):
    def __init__(self,edgetype):
        self.Type = edgetype


class FredGraph:
    def __init__(self,rdf):
        self.rdf = rdf

    def __str__(self):
        return json.dumps(self.to_dict(),
                   indent=4,
                   default=str)

    def getNodes(self):
        nodes = list()
        for a, b, c in self.rdf:
            nodes.append(a.strip())
            nodes.append(c.strip())
        return nodes

    def getClassNodes(self):
        query = "PREFIX owl: <http://www.w3.org/2002/07/owl#> " \
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                "SELECT ?t WHERE { " \
                "?i a ?t1 . " \
                "?t1 (owl:equivalentClass | ^owl:equivalentClass | rdfs:sameAs | ^rdfs:sameAs | rdfs:subClassOf)* ?t }"

        nodes = list()
        res = self.rdf.query(query)
        for el in res:
            nodes.append(el[0].strip())
        return nodes

    def getInstanceNodes(self):
        nodes = set(self.getNodes())\
            .difference(set(self.getClassNodes()))
        return list(nodes)

    def getEventNodes(self):
        query = "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#> " \
                "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                "SELECT ?e WHERE { ?e a ?t . ?t rdfs:subClassOf* dul:Event }"

        nodes = list()
        res = self.rdf.query(query)
        for el in res:
            nodes.append(el[0].strip())
        return nodes

    def getSituationNodes(self):
        query = "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#> " \
                "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                "SELECT ?e WHERE { ?e a ?t . ?t rdfs:subClassOf* boxing:Situation }"

        nodes = list()
        res = self.rdf.query(query)
        for el in res:
            nodes.append(el[0].strip())
        return nodes

    def getNamedEntityNodes(self):
        nodes = self.getNodes()
        events = self.getEventNodes()
        classes = self.getClassNodes()
        qualities = self.getQualityNodes()
        situation = self.getSituationNodes()

        ne = list()
        for n in nodes:
            if n not in classes and n not in qualities and n not in events and n not in situation:
                suffix = n[n.find("_", -1):]
                if suffix.isdigit() == False:
                    ne.append(n)
        return ne

    def getSkolemizedEntityNodes(self):
        nodes = self.getNodes()
        events = self.getEventNodes()
        classes = self.getClassNodes()
        qualities = self.getQualityNodes()
        situation = self.getSituationNodes()

        ne = list()
        for n in nodes:
            if n not in classes and n not in qualities and n not in events and n not in situation:
                suffix = n[n.find("_", -1):]
                if suffix.isdigit() == True:
                    ne.append(n)
        return ne

    def getQualityNodes(self):
        query = "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                "SELECT ?q WHERE { ?i dul:hasQuality ?q }"
        nodes = list()
        res = self.rdf.query(query)
        for el in res:
            nodes.append(el[0].strip())
        return nodes

    def getConceptNodes(self):
        return self.getClassNodes()

    #return 1 for situation, 2 for event, 3 for named entity, 4 for concept class, 5 for concept instance
    def getInfoNodes(self):

        def getResource(n):
            if node.find("http://www.ontologydesignpatterns.org/ont/dbpedia/")==0:
                return ResourceType.Dbpedia
            elif node.find("http://www.ontologydesignpatterns.org/ont/vn/")==0:
                return ResourceType.Verbnet
            else:
                return ResourceType.Fred

        nodes = dict()
        query = "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#> " \
                "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                "SELECT ?n ?class ?x WHERE { { ?n a ?t . ?t rdfs:subClassOf* boxing:Situation bind (1 as ?x) bind (0 as ?class) } " \
                "UNION {?n a ?t . ?t rdfs:subClassOf* dul:Event bind (2 as ?x)  bind (0 as ?class)} " \
                "UNION {?i a ?t . ?t (owl:equivalentClass | ^owl:equivalentClass | rdfs:sameAs | ^rdfs:sameAs | rdfs:subClassOf)* ?n bind (6 as ?x) bind (1 as ?class)} }"

        res = self.rdf.query(query)
        for el in res:
            node = el[0].strip()
            cl = NodeType(el[1].value)
            type = FredType(el[2].value)
            nodes[node] = FredNode(cl,type,getResource(node))

        #if not an event nor situation nor class

        qualities = self.getQualityNodes()
        for n in qualities:
            if n not in nodes:
                nodes[n] = FredNode(NodeType.Instance,FredType.Quality,getResource(n))

        #if not even quality

        for n in self.getNodes():
            if n not in nodes:
                suffix = n[n.find("_", -1):]
                if n not in qualities and suffix.isdigit() == False:
                    nodes[n] = FredNode(NodeType.Instance,FredType.NamedEntity,getResource(n))
                else:
                    nodes[n] = FredNode(NodeType.Instance,FredType.SkolemizedEntity,getResource(n))

        return nodes

    def getEdges(self):
        return [(a.strip(),b.strip(),c.strip()) for (a,b,c) in self.rdf]

    #def getRoleEdges(self):
    #    return self.getEdgeMotif(EdgeMotif.Role)

    def getEdgeMotif(self,motif):
        if motif == EdgeMotif.Role:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . ?i a ?t . ?t rdfs:subClassOf* dul:Event BIND (5 as ?r) }"
        elif motif == EdgeMotif.Identity:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . FILTER(?p = owl:sameAs ) BIND (1 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}}"
        elif motif == EdgeMotif.Type:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . FILTER(?p = rdf:type ) BIND (2 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}}"
        elif motif == EdgeMotif.SubClass:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . FILTER(?p = rdfs:subClassOf ) BIND (3 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}}"
        elif motif == EdgeMotif.Equivalence:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . FILTER(?p = owl:equivalentClass ) BIND (4 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}}"
        elif motif == EdgeMotif.Modality:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . FILTER(?p = boxing:hasModality ) BIND (6 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}}"
        elif motif == EdgeMotif.Negation:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . FILTER(?p = boxing:hasTruthValue ) BIND (7 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}}"
        elif motif == EdgeMotif.Property:
            query = "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
                    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "SELECT ?i ?p ?o ?r WHERE " \
                    "{?i ?p ?o . " \
                    "FILTER((?p != owl:sameAs) && (?p != rdf:type) && (?p != rdfs:subClassOf) && (?p != owl:equivalentClass) && (?p != boxing:hasModality) && (?p != boxing:hasTruthValue)) " \
                    "FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event} " \
                    "BIND (8 as ?r) }"
        else:
            raise Exception("Unknown motif: " + str(motif))

        return [(el[0].strip(),el[1].strip(),el[2].strip()) for el in self.rdf.query(query)]

    def getPathMotif(self,motif):
        if motif == PathMotif.Type:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT ?i ?o WHERE " \
                    "{?i rdf:type ?t . ?t rdfs:subClassOf* ?o}"
        elif motif == PathMotif.SubClass:
            query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT ?i ?o WHERE " \
                    "{?i rdfs:subClassOf+ ?o}"
        else:
            raise Exception("Unknown motif: " + str(motif))

        return [(el[0].strip(),el[1].strip()) for el in self.rdf.query(query)]

    def getClusterMotif(self,motif):
        if motif == ClusterMotif.Identity:
            query = "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT DISTINCT ?s ?o WHERE " \
                    "{ ?s (owl:sameAs|^owl:sameAs)+ ?o } ORDER BY ?s "
        elif motif == ClusterMotif.Equivalence:
            query = "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT DISTINCT ?s ?o WHERE " \
                    "{ ?s (^owl:equivalentClass|owl:equivalentClass)+ ?o } ORDER BY ?s "
        elif motif == ClusterMotif.IdentityEquivalence:
            query = "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                    "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                    "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
                    "SELECT DISTINCT ?s ?o WHERE " \
                    "{ ?s (owl:sameAs|^owl:sameAs|^owl:equivalentClass|owl:equivalentClass)+ ?o } ORDER BY ?s "
        else:
            raise Exception("Unknown motif: " + str(motif))

        results = self.rdf.query(query)

        clusters = list()
        used = set()
        olds = None
        currentset = set()
        for el in results:
            s = el[0].strip()
            o = el[1].strip()
            if s != olds:
                if len(currentset) != 0:
                    currentset.add(olds)
                    clusters.append(currentset)
                    used = used.union(currentset)
                    currentset = set()
                fillSet = False if s in used else True
            if fillSet == True:
                currentset.add(o)
            olds = s

        if len(currentset) != 0:
            currentset.add(olds)
            clusters.append(currentset)

        return clusters

    # def getInfoEdges(self):
    #     edges = dict()
    #     query = "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#> " \
    #             "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> " \
    #             "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#> " \
    #             "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
    #             "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
    #             "" \
    #             "SELECT ?i ?p ?o ?r WHERE {" \
    #             "{?i ?p ?o . ?i a ?t . ?t rdfs:subClassOf* dul:Event BIND (5 as ?r) }" \
    #             "UNION" \
    #             "{?i ?p ?o . FILTER(?p = owl:sameAs ) BIND (1 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}  }" \
    #             "UNION" \
    #             "{?i ?p ?o . FILTER(?p = rdf:type ) BIND (2 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}  }" \
    #             "UNION" \
    #             "{?i ?p ?o . FILTER(?p = rdfs:subClassOf ) BIND (3 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}  }" \
    #             "UNION" \
    #             "{?i ?p ?o . FILTER(?p = owl:equivalentClass ) BIND (4 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}  }" \
    #             "UNION" \
    #             "{?i ?p ?o . FILTER(?p = boxing:hasModality ) BIND (6 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}  }" \
    #             "UNION" \
    #             "{?i ?p ?o . FILTER(?p = boxing:hasTruthValue ) BIND (7 as ?r) FILTER NOT EXISTS {?i a ?t . ?t rdfs:subClassOf* dul:Event}  }" \
    #             "}"
    #
    #     res = self.rdf.query(query)
    #     for el in res:
    #         edges[(el[0].strip(),el[1].strip(),el[2].strip())] = FredEdge(EdgeMotif(el[3].value))
    #     for e in self.getEdges():
    #         if e not in edges:
    #             edges[e] = FredEdge(EdgeMotif.Property)
    #     return edges

    def getNaryMotif(self,motif):
        def fillRoles(el):
            relations = dict()
            if el['agent'] != None:
                relations[Role.Agent] = el['agent']
            if el['patient'] != None:
                relations[Role.Patient] = el['patient']
            if el['theme'] != None:
                relations[Role.Theme] = el['theme']
            if el['location'] != None:
                relations[Role.Theme] = el['location']
            if el['time'] != None:
                relations[Role.Theme] = el['time']
            if el['involve'] != None:
                relations[Role.Theme] = el['involve']
            if el['declared'] != None:
                relations[Role.Theme] = el['declared']
            if el['vnoblique'] != None:
                relations[Role.Theme] = el['vnoblique']
            if el['locoblique'] != None:
                relations[Role.Theme] = el['locoblique']
            if el['conjoblique'] != None:
                relations[Role.Theme] = el['conjoblique']
            if el['extended'] != None:
                relations[Role.Theme] = el['extended']
            if el['associated'] != None:
                relations[Role.Theme] = el['associated']
            return relations

        query = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> " \
                "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> " \
                "PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#>" \
                "PREFIX vnrole: <http://www.ontologydesignpatterns.org/ont/vn/abox/role/>" \
                "PREFIX boxing: <http://www.ontologydesignpatterns.org/ont/boxer/boxing.owl#>" \
                "PREFIX boxer: <http://www.ontologydesignpatterns.org/ont/boxer/boxer.owl#>" \
                "PREFIX d0: <http://www.ontologydesignpatterns.org/ont/d0.owl#>" \
                "PREFIX schemaorg: <http://schema.org/>" \
                "PREFIX earmark: <http://www.essepuntato.it/2008/12/earmark#>" \
                "PREFIX fred: <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#>" \
                "PREFIX wn: <http://www.w3.org/2006/03/wn/wn30/schema/>" \
                "PREFIX pos: <http://www.ontologydesignpatterns.org/ont/fred/pos.owl#>" \
                "PREFIX semiotics: <http://ontologydesignpatterns.org/cp/owl/semiotics.owl#>" \
                "PREFIX owl: <http://www.w3.org/2002/07/owl#>" \
                "SELECT DISTINCT" \
                "?node ?type " \
                "?agentiverole ?agent" \
                "?passiverole ?patient" \
                "?themerole ?theme" \
                "?locativerole ?location" \
                "?temporalrole ?time" \
                "?situationrole ?involve" \
                "?declarationrole ?declared" \
                "?vnobrole ?vnoblique" \
                "?preposition ?locoblique" \
                "?conjunctive ?conjoblique" \
                "?periphrastic ?extended" \
                "?associationrole ?associated " \
                "WHERE " \
                "{" \
                "{{?node rdf:type ?concepttype bind (4 as ?type)" \
                "MINUS {?node rdf:type rdf:Property}" \
                "MINUS {?node rdf:type owl:ObjectProperty}" \
                "MINUS {?node rdf:type owl:DatatypeProperty}" \
                "MINUS {?node rdf:type owl:Class}" \
                "MINUS {?node rdf:type earmark:PointerRange}" \
                "MINUS {?node rdf:type earmark:StringDocuverse}" \
                "MINUS {?concepttype rdfs:subClassOf+ dul:Event}" \
                "MINUS {?node rdf:type boxing:Situation}" \
                "MINUS {?concepttype rdfs:subClassOf+ schemaorg:Event}" \
                "MINUS {?concepttype rdfs:subClassOf+ d0:Event}}" \
                "}" \
                "UNION " \
                " {?node rdf:type boxing:Situation bind (2 as ?type)}" \
                "UNION" \
                " {?node rdf:type ?verbtype . ?verbtype rdfs:subClassOf* dul:Event bind (1 as ?type)}" \
                "UNION" \
                " {?node rdf:type ?othereventtype . ?othereventtype rdfs:subClassOf* schemaorg:Event bind (3 as ?type)}" \
                "UNION" \
                " {?node rdf:type ?othereventtype . ?othereventtype rdfs:subClassOf* d0:Event bind (3 as ?type)}" \
                "OPTIONAL " \
                " {?node ?agentiverole ?agent" \
                " FILTER (?agentiverole = vnrole:Agent || ?agentiverole = vnrole:Actor1 || ?agentiverole = vnrole:Actor2 || ?agentiverole = vnrole:Experiencer || ?agentiverole = vnrole:Cause || ?agentiverole = boxer:agent)}" \
                "OPTIONAL " \
                " {?node ?passiverole ?patient" \
                " FILTER (?passiverole = vnrole:Patient || ?passiverole = vnrole:Patient1 || ?passiverole = vnrole:Patient2 || ?passiverole = vnrole:Beneficiary || ?passiverole = boxer:patient || ?passiverole = vnrole:Recipient || ?passiverole = boxer:recipient)} " \
                "OPTIONAL " \
                " {?node ?themerole ?theme" \
                " FILTER (?themerole = vnrole:Theme || ?themerole = vnrole:Theme1 || ?themerole = vnrole:Theme2 || ?themerole = boxer:theme)} " \
                "OPTIONAL " \
                " {?node ?locativerole ?location" \
                " FILTER (?locativerole = vnrole:Location || ?locativerole = vnrole:Destination || ?locativerole = vnrole:Source || ?locativerole = fred:locatedIn)} " \
                "OPTIONAL " \
                " {?node ?temporalrole ?time" \
                " FILTER (?temporalrole = vnrole:Time)} " \
                "OPTIONAL " \
                " {?node ?situationrole ?involve" \
                " FILTER (?situationrole = boxing:involves)} " \
                "OPTIONAL " \
                " {?node ?declarationrole ?declared" \
                " FILTER (?declarationrole = boxing:declaration || ?declarationrole = vnrole:Predicate || ?declarationrole = vnrole:Proposition)} " \
                "OPTIONAL " \
                " { ?node ?vnobrole ?vnoblique " \
                " FILTER (?vnobrole = vnrole:Asset || ?vnobrole = vnrole:Attribute || ?vnobrole = vnrole:Extent || ?vnobrole = vnrole:Instrument || ?vnobrole = vnrole:Material || ?vnobrole = vnrole:Oblique || ?vnobrole = vnrole:Oblique1 || ?vnobrole = vnrole:Oblique2 || ?vnobrole = vnrole:Product || ?vnobrole = vnrole:Stimulus || ?vnobrole = vnrole:Topic || ?vnobrole = vnrole:Value)}" \
                "OPTIONAL " \
                " {?node ?preposition ?locoblique" \
                " FILTER (?preposition = fred:about || ?preposition = fred:after || ?preposition = fred:against || ?preposition = fred:among || ?preposition = fred:at || ?preposition = fred:before || ?preposition = fred:between || ?preposition = fred:by || ?preposition = fred:concerning || ?preposition = fred:for || ?preposition = fred:from || ?preposition = fred:in || ?preposition = fred:in_between || ?preposition = fred:into || ?preposition = fred:of || ?preposition = fred:off || ?preposition = fred:on || ?preposition = fred:onto || ?preposition = fred:out_of || ?preposition = fred:over || ?preposition = fred:regarding || ?preposition = fred:respecting || ?preposition = fred:through || ?preposition = fred:to || ?preposition = fred:towards || ?preposition = fred:under || ?preposition = fred:until || ?preposition = fred:upon || ?preposition = fred:with)}" \
                "OPTIONAL " \
                " {{?node ?conjunctive ?conjoblique" \
                " FILTER (?conjunctive = fred:as || ?conjunctive = fred:when || ?conjunctive = fred:after || ?conjunctive = fred:where || ?conjunctive = fred:whenever || ?conjunctive = fred:wherever || ?conjunctive = fred:because || ?conjunctive = fred:if || ?conjunctive = fred:before || ?conjunctive = fred:since || ?conjunctive = fred:unless || ?conjunctive = fred:until || ?conjunctive = fred:while)} UNION {?conjoblique ?conjunctive ?node FILTER (?conjunctive = fred:once || ?conjunctive = fred:though || ?conjunctive = fred:although)}}" \
                "OPTIONAL " \
                " {?node ?periphrastic ?extended" \
                " FILTER (?periphrastic != ?vnobrole && ?periphrastic != ?preposition && ?periphrastic != ?conjunctive && ?periphrastic != ?agentiverole && ?periphrastic != ?passiverole && ?periphrastic != ?themerole && ?periphrastic != ?locativerole && ?periphrastic != ?temporalrole && ?periphrastic != ?situationrole && ?periphrastic != ?declarationrole && ?periphrastic != ?associationrole && ?periphrastic != boxing:hasTruthValue && ?periphrastic != boxing:hasModality && ?periphrastic != dul:hasQuality && ?periphrastic != dul:associatedWith && ?periphrastic != dul:hasRole &&?periphrastic != rdf:type)}" \
                "OPTIONAL " \
                " {?node ?associationrole ?associated" \
                " FILTER (?associationrole = boxer:rel || ?associationrole = dul:associatedWith)} " \
                "}" \
                " ORDER BY ?type"

        results = self.rdf.query(query)
        motifocc = dict()
        for el in results:
            if NaryMotif(el['type']) == motif:
                motifocc[el['node'].strip()] = fillRoles(el)

        return motifocc


    # Structure Validation
    # ------------------------------------------------------------------------------------------------------------------
    def keys_to_str(self, obj):
        if isinstance(obj, dict):
            return {str(k): self.keys_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.keys_to_str(i) for i in obj]
        else:
            return obj


    def to_dict(self, simple=False):
        output = dict()

        def clean(uri:str):
            return clean_uri(uri) if simple else uri

        def clean_tuple(t:tuple):
            if len(t) != 3:
                raise ValueError(f"Error: expecting tuple of length 3, tuple {t} was only {len(t)} entries long")

            return [clean(t[0]), clean(t[1]), clean(t[2])]

        node_methods = [
            ("getNodes", self.getNodes),
            ("getClassNodes", self.getClassNodes),
            ("getInstanceNodes", self.getInstanceNodes),
            ("getEventNodes", self.getEventNodes),
            ("getSituationNodes", self.getSituationNodes),
            ("getNamedEntityNodes", self.getNamedEntityNodes),
            ("getQualityNodes", self.getQualityNodes)
        ]
        for header, func in node_methods:
            output[header] = [clean(n) for n in func()]

        output["getInfoNodes"] = dict()
        infoNodes = self.getInfoNodes()
        for n in infoNodes:
            output["getInfoNodes"][clean(str(n))] = {
                "type": infoNodes[n].Type,
                "FredType": infoNodes[n].FredType,
                "ResourceType": infoNodes[n].ResourceType
            }

        # Get edge triples
        output["getEdges"] = [clean_tuple(e) for e in self.getEdges()]

        # Edge motifs
        motifs = [
            ("Role", EdgeMotif.Role),
            ("Identity", EdgeMotif.Identity),
            ("Type", EdgeMotif.Type),
            ("SubClass", EdgeMotif.SubClass),
            ("Equivalence", EdgeMotif.Equivalence),
            ("Modality", EdgeMotif.Modality),
            ("Negation", EdgeMotif.Negation),
            ("Property", EdgeMotif.Property),
        ]
        output["getEdgeMotif"] = dict()
        for label, motif in motifs:
            output["getEdgeMotif"][label] = [clean_tuple(e) for e in self.getEdgeMotif(motif)]

        # # Get info edges
        # output["getInfoEdges"] = dict()
        # info_edges = self.getInfoEdges()
        # for e in info_edges:
        #     edge_type = str(info_edges[e].Type)
        #     # if the edge type isn't in the set of info edges, and it's not in the list of edge motifs
        #     if edge_type not in output["getInfoEdges"].keys()\
        #             and edge_type.split(".")[-1] not in output["getEdgeMotif"].keys():
        #         output["getInfoEdges"][edge_type] = list()
        #     # if it's been added to the list of edges
        #     if edge_type in output["getInfoEdges"].keys():
        #         output["getInfoEdges"][edge_type].append(clean_tuple(e))

        # Get path motifs
        path_motifs = [
            ("Type", PathMotif.Type),
            ("SubClass", PathMotif.SubClass),
        ]
        output["getPathMotif"] = dict()
        for label, motif in path_motifs:
            output["getPathMotif"][label] = [[clean(m), clean(n)] for m, n in self.getPathMotif(motif)]

        # Get cluster motifs
        cluster_motifs = [
            ("Identity", ClusterMotif.Identity),
            ("Equivalence", ClusterMotif.Equivalence),
            ("IdentityEquivalence", ClusterMotif.IdentityEquivalence),
        ]
        output["getClusterMotif"] = dict()
        for label, motif in cluster_motifs:
            output["getClusterMotif"][label] = list()
            for cluster in self.getClusterMotif(motif):
                output["getClusterMotif"][label].append(clean(str(cluster)))

        # Get N-ary motifs
        nary_motifs = [
            ("Event", NaryMotif.Event),
            ("Situation", NaryMotif.Situation),
            ("OtherEvent", NaryMotif.OtherEvent),
            ("Concept", NaryMotif.Concept),
        ]
        output["getNaryMotif"] = dict()
        for label, motif in nary_motifs:
            output["getNaryMotif"][label] = [clean(n) for n in self.getNaryMotif(motif)]

        return self.keys_to_str(output)


# Processing Functions
# ----------------------------------------------------------------------------------------------------------------------
def preprocessText(text):
    # Original text cleanup
    nt = text.replace("-", " ").replace("#", " ").replace(chr(96), "'")

    # Dictionary of replacements
    replacements = {
        "'nt ": " not ",
        "'ve ": " have ",
        " what's ": " what is ",
        "What's ": "What is ",
        " where's ": " where is ",
        "Where's ": "Where is ",
        " how's ": " how is ",
        "How's ": "How is ",
        " he's ": " he is ",
        " she's ": " she is ",
        " it's ": " it is ",
        "He's ": "He is ",
        "She's ": "She is ",
        "It's ": "It is ",
        "'d ": " had ",
        "'ll ": " will ",
        "'m ": " am ",
        " ma'am ": " madam ",
        " o'clock ": " of the clock ",
        " 're ": " are ",
        " y'all ": " you all "
    }

    # Apply replacements
    for old, new in replacements.items():
        nt = nt.replace(old, new)

    nt = nt.strip()
    if nt[len(nt)-1]!='.':
        nt = nt + "."

    return nt

def getFredGraph(text:str,
                 key:str,
                 filename:str,
                 prefix:str = "fred:",
                 namespace:str = "http://www.ontologydesignpatterns.org/ont/fred/domain.owl#",
                 wsd:bool = False,
                 wfd:bool = False,
                 wfd_profile:str = 'b',
                 tense:bool = False,
                 roles:bool = False,
                 textannotation:str = "earmark",
                 semantic_subgraph:bool = False,
                 response_format:str = "application/rdf+xml"
                 ):

    # keyword validation
    if wfd_profile not in {'b', 'd', 't'}:
        raise KeyError(f"ERROR: Invalid wfd_profile: {wfd_profile} not in ['b', 'd', 't'].")
    if textannotation not in {"earmark", "nif"}:
        raise KeyError(f"ERROR: Invalid textannotation: {textannotation} not in ['earmark', 'nif'].")

    valid_response_formats = {
        "application/rdf+xml",
        "text/turtle",
        "application/rdf+json",
        "text/rdf+n3",
        "text/rdf+nt",
        "image/png",
    }
    if response_format not in valid_response_formats:
        raise KeyError(f"ERROR: Invalid response_format: {response_format} not in {valid_response_formats}.")

    command_to_exec = [
        "curl -G -X GET",
        f"-H \"Accept: {response_format}\"",
        f"-H \"Authorization: Bearer {key}\"",
        f"--data-urlencode text=\"{text}\"",
        f"-d prefix=\"{prefix}\"",
        f"--data-urlencode namespace=\"{namespace}\"",
        f"-d wsd=\"{(str(wsd)).lower()}\"",
        f"-d wfd=\"{(str(wfd)).lower()}\"",
        f"-d wfd-profile=\"{wfd_profile}\"",
        f"-d tense=\"{(str(tense)).lower()}\"",
        f"-d roles=\"{(str(roles)).lower()}\"",
        f"-d textannotation=\"{textannotation}\"",
        f"-d semantic-subgraph=\"{(str(semantic_subgraph)).lower()}\"",
        "http://wit.istc.cnr.it/stlab-tools/fred >",
        filename
    ]
    try:
        os.system(" ".join(command_to_exec))
    except:
        print("error os running curl FRED")
        sys.exit(1)

    return openFredGraph(filename)

def openFredGraph(filename):
    rdf = rdflib.Graph()
    rdf.parse(filename)
    return FredGraph(rdf)


# Visualization Functions
# ----------------------------------------------------------------------------------------------------------------------
import networkx as nx

def clean_uri(uri):
    # ex: 'http://www.ontologydesignpatterns.org/ont/fred/domain.owl#Motion_directional_1'
    # ex: 'http://www.ontologydesignpatterns.org/ont/framenet/abox/fe/Patient.ingestion'
    split_uri = str(uri).split("/")
    entity_label = split_uri[-1]
    return entity_label.replace("#", ": ")


def get_simplified_nx_graph(g):
    simplified_g = [(clean_uri(triple[0]),
                     clean_uri(triple[2]),
                     clean_uri(triple[1]))
                    for triple in g]

    for triple in simplified_g:
        print(triple)

    G = nx.DiGraph()

    for source, target, relation in simplified_g:
        G.add_edge(source, target, labels=relation)

    return G

import math
import matplotlib.pyplot as plt

def plot_graph(G, scaling=50, edge_width=1, k=2):
    # Calculate figure size based on the number of nodes
    num_nodes = len(G.nodes)
    num_edges = len(G.edges)
    graph_size = (num_nodes) + (2 * num_edges)

    figsize = graph_size * scaling / 300
    font_size = 2 + math.sqrt(scaling) / 5
    # Calculate node sizes based on the length of the token text
    node_sizes = [scaling * int(math.log2(len(node))) for node in G.nodes()]

    # Position nodes using the spring layout
    pos = nx.spring_layout(G, seed=42, k=k / num_nodes)
    plt.figure(figsize=(figsize, figsize), dpi=300)

    # Draw nodes with sizes proportional to the length of their text
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes)
    # Draw node labels
    nx.draw_networkx_labels(G, pos, font_size=font_size, font_family="sans-serif")


    # Draw edges with widths based on edge weights
    nx.draw_networkx_edges(G,
                           pos,
                           width=edge_width,
                           arrows=True,
                           arrowstyle='-|>',
                           connectionstyle="arc3,rad=0.2")
    # # Draw edge labels
    edge_labels = nx.get_edge_attributes(G, "labels")
    nx.draw_networkx_edge_labels(G,
                                  pos,
                                  edge_labels=edge_labels,
                                  font_size=font_size,
                                  label_pos=0.5,
                                  rotate=False)

    # Customize and show plot
    ax = plt.gca()
    ax.margins(0.08)
    plt.axis("off")
    plt.tight_layout()

    plt.show()

# Example usage
# if __name__ == "__main__":
#     g = checkFredSentence('The radio said that Pippo went to France', sys.argv[1],'pippo.rdf')