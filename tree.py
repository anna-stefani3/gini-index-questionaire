class TREE:
    def __init__(self, question, choices, score, question_queue, level):
        self.question = question
        self.score = score
        self.choices = choices
        self.children = []
        self.best = None
        self.question_queue = question_queue
        self.level = level

    def add_child_node(self, child_node):
        self.children.extend(child_node)

    def get_best_score(self):
        best = self.score
        if self.children:
            for child in self.children:
                child_best = child.get_best_score()
                if child_best < best:
                    best = child_best
        return best

    def __repr__(self):
        return (
            f"Question: {self.question.ljust(25)} "
            f"| Score : {str(self.score).ljust(5)} "
            f"| Choices : {self.choices if len(self.choices) < 4 else len(self.choices)} "
        )

    def print_(self):
        spaces = " " * self.level * 24
        prefix = spaces + "|___ "
        print(prefix, self.__repr__())
        if self.children:
            for child in self.children:
                child.print_()
