class NODE:
    def __init__(self, question, choices, score, question_queue, level):
        # stores the Column Name
        self.question = question

        # stores the score for this Question
        self.score = score

        # stores the choices for this Question
        self.choices = choices

        # stores all child Node for this Node Question
        self.children = []

        # stores the best scores from all child and root Node
        self.best = None

        # stores the question Queue that can be asked next level
        self.question_queue = question_queue

        # stores the level at which this node currently is
        self.level = level

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

    def get_best_score(self):
        """
        Process:
            stores the current Node Score, then looks deep into all child node
            to get the best score among all root node or child nodes.
        """
        best = self.score
        if self.children:
            for child in self.children:
                child_best = child.get_best_score()
                """
                    Checking for lower score(best Score)
                """
                if child_best < best:
                    best = child_best
        return best

    def __repr__(self):
        """
        Used to Show the TREE Object in Readable Form
        """
        return (
            f"Question: {self.question.ljust(25)} "
            f"| Score : {str(self.score).ljust(5)} "
            f"| Choices : {self.choices if len(self.choices) < 4 else len(self.choices)} "
        )

    def print_(self):
        """
        Used to parse through all node and show the tree like structure of the Root Node
        The tree like structure printed in console is from this function
        """
        spaces = " " * self.level * 24
        prefix = spaces + "|___ "
        print(prefix, self.__repr__())
        if self.children:
            for child in self.children:
                child.print_()
