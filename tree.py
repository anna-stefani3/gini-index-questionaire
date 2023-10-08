import random


class TREE:
    def __init__(self, question, choices, score=None):
        self.question = question
        self.score = score
        self.choices = choices
        self.parent = None
        self.children = []
        self.best = self.get_best_score()

    def add_child(self, child_node):
        child_node.parent = self
        self.children.append(child_node)
        self.best = self.get_best_score()

    def get_best_score(self):
        best = self.score
        if self.children:
            for child in self.children:
                child_best = child.get_best_score()
                if child_best < best:
                    best = child_best
        return best

    def get_level(self):
        level = 0
        p = self.parent
        while p:
            level = level + 1
            p = p.parent
        return level

    def print_(self):
        spaces = " " * self.get_level() * 6
        prefix = "|" + spaces + "|___ " if self.parent else "|_ "
        print(prefix + self.question, self.score)
        if self.children:
            for child in self.children:
                child.print_()


if __name__ == "__main__":

    def random_score():
        return round(random.randint(0, 10000) / 20000, 4)

    gender = TREE("gender", [0, 1], random_score())
    category = TREE("category", [0, 1], random_score())

    hunger = TREE("hunger", [0, 1], random_score())
    emotion = TREE("emotion", [0, 1], random_score())
    mental = TREE("mental", [0, 1], random_score())

    # hunger
    hunger_level = TREE("hunger_level", [0, 1, 2], random_score())

    # emotion
    anger = TREE("anger", [0, 1, 2], random_score())
    happy = TREE("happy", [0, 1, 2], random_score())
    sad = TREE("sad", [0, 1, 2], random_score())

    # mental
    depression = TREE("depression", [0, 1, 2], random_score())
    suicidal = TREE("suicidal", [0, 1, 2], random_score())
    exhausted = TREE("exhausted", [0, 1, 2], random_score())

    hunger.add_child(hunger_level)

    emotion.add_child(anger)
    emotion.add_child(happy)
    emotion.add_child(sad)

    mental.add_child(depression)
    mental.add_child(suicidal)
    mental.add_child(exhausted)

    gender.add_child(hunger)
    gender.add_child(emotion)

    category.add_child(mental)

    gender.print_()

    category.print_()

    print(emotion.__dict__["best"])
    print(category.best)
