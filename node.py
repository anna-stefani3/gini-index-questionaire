from graphviz import Digraph


class NODE:
    def __init__(self, question, score):
        # stores the Column Name
        self.question = question

        # stores the score for this Question
        self.score = score

        # stores all child Node for this Node Question
        self.children = []

        # stores the best scores from all child and root Node
        self.best = None

    def add_child_node(self, child_node):
        """
        input:
        child_node -> TREE or Array[TREE]

        output:
        adds or extends the child node to this.children list

        example
        when Node is TREE Append is used
            then this.children from [Node1, Node2] becomes [Node1, Node2, Node3]

        When Node is [TREE] Extend is used
            then this.children from [Node1, Node2] becomes [Node1, Node2, Node3]
        """
        if type(child_node) == list:
            self.children.extend(child_node)
        else:
            self.children.append(child_node)

    def update_best_scores(self):
        """
        Process:
            stores the current Node Score, then looks deep into all child node
            to get the best score among all root node or child nodes.
        """
        self.best = self.score
        if self.children:
            for child in self.children:
                child_best = child.update_best_scores()
                """
                    Checking for lower score(best Score)
                """
                if child_best < self.best:
                    self.best = child_best
        return self.best

    def __repr__(self):
        """
        Used to Show the TREE Object in Readable Form
        """
        return f"{self.question}___{self.best}"

    def to_graphviz(self, parent=None, graph=None):
        if graph is None:
            graph = Digraph(format='png')
            graph.node(self.__repr__())

        if parent is not None:
            graph.edge(parent.__repr__(), self.__repr__())

        for child in self.children:
            child.to_graphviz(self, graph)

        return graph

    def visualize_tree(self):
        graph = self.to_graphviz()

        # Render the graph to a file
        graph.render(filename="generated_output/" + self.question, format='png', cleanup=True)
