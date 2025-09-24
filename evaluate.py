from rdflib import Graph, RDF, OWL, Namespace
from rdflib.namespace import RDF, RDFS
from rdflib.term import URIRef


class Evaluator:
    """
    Allows evaluating simplified DL expressions over an RDFLib graph.
    """

    def __init__(self, path):
        self.graph = Graph()
        self.graph.parse(path)
        self.uri = dict(self.graph.namespace_manager.namespaces())[""]

        # Run materialization up front so later queries see implied facts.
        self.materialize()
        
    def materialize(self) -> None:
      for s, _, o in self.graph.triples((None, RDF.type, None)):

        supers = []
        while any(self.graph.triples((o, RDFS.subClassOf, None))):
          for _, _, n in self.graph.triples((o, RDFS.subClassOf, None)):
              supers.append(n)
              o = n
        for o in supers:
          self.graph.add((s, RDF.type, o))


          
    def parse(self, expression:str):
        expr = expression.replace(" ", "").replace("(", "").replace(")", "")
        l = expr.split("⊔")
        for i, e in enumerate(l):
           l[i] = e.split("⊓")
           for i2, j in enumerate(l[i]):
                if j.startswith("∀"):
                    l[i][i2] = {"type": "all", "role": j.removeprefix("∀").split(".")[0] , "name": j.removeprefix("∀").split(".")[1]}
                elif j.startswith("∃"):
                    l[i][i2] = {"type": "exists", "role": j.removeprefix("∃").split(".")[0] , "name": j.removeprefix("∃").split(".")[1]}
                elif j.startswith("¬"):
                    l[i][i2] = {"type": "not", "name": j.removeprefix("¬")}
                else:
                    l[i][i2] = {"type": "atomic", "name" : j}
        return l 
        """"
        Entry point for the Parsing task.
        
        The goal is to transform the given string such that you can evaluate it easier. You are not expected to write a full grammar.
        
        As the parsing has no fixed output datastructure it does not have a preimplemented test. You may implement your own, if that helps your debugging.

        Input language (restricted DNF):
          - Overall form: disjunction of conjunctions.
              Example:  (A ⊓ ∀R.C) ⊔ (¬A ⊓ B)
              (For more examples see the test case)
          - Allowed operators are: ¬, ⊓, ⊔, ∃, ∀
          - Negation applies only to atomic concepts (e.g., ¬A is allowed; ¬(A ⊓ B), ∃R.¬A, or ¬∀R.A are NOT).
          
        """
    def evaluate(self, expression: str) -> set:
        parsed = self.parse(expression)
        individuals = {x for x in set(self.graph.subjects(RDF.type, None))if x not in  set(self.graph.subjects(RDF.type, RDFS.Class)) | set(self.graph.subjects(RDF.type, OWL.Class))|set(self.graph.subjects(RDF.type, RDF.Property))}
        for i, d in enumerate(parsed):
            for i2, e in enumerate(d):
                hits = set()
                for individual in individuals:
                    if e["type"] == "all":
                        hit = True
                        role = self.get_uri(e["role"])
                        class_uri = self.get_uri(e["name"])
                        targets = self.graph.objects(individual, role)
                        for o in targets:
                            if (o, RDF.type, class_uri) not in self.graph:
                                hit = False
                                break
                        if hit: 
                            hits.add(individual)
                    if e["type"] == "exists":
                        hit = False
                        role = self.get_uri(e["role"])
                        class_uri = self.get_uri(e["name"])
                        targets = self.graph.objects(individual, role)
                        for o in targets:
                            if (o, RDF.type, class_uri) in self.graph:
                                hit = True
                                break
                        if hit:
                             hits.add(individual)
                    if e["type"] == "not":
                        hit = True
                        for _, _, o in self.graph.triples((individual, RDF.type, None)):
                            if o == self.get_uri(e["name"]):
                                hit = False
                        if hit:
                            hits.add(individual)
                    if e["type"] == "atomic":
                        hit = False
                        for _, _, o in self.graph.triples((individual, RDF.type, None)):
                            if o == self.get_uri(e["name"]):
                                hit = True
                        if hit:
                            hits.add(individual)
                parsed[i][i2] = hits
            parsed[i] = set.intersection(*parsed[i]) if parsed[i] else set()
        return set.union(*parsed) if parsed else set()

                              
        """
        Entry point for the Evaluation task.
            
        Returns:
          set[URIRef]: Individuals in the graph that satisfy the expression.
        """
        expression = self.parse(expression)
        pass
    
    #----------------------------------------------------------------#
    
    def get_uri(self, rdf_term: str) -> URIRef:
        """Helper function that constructs a URI reference object for the RDF term given as str.
        
        Use it when you need to construct a URIRef object, e.g. get_uri("person") to get the URIRef of the concept person.
        
        The given data includes the concepts person, male, female, father, mother; the property hasChild; and eight related individuals.
        """
        return URIRef(self.uri + rdf_term)
