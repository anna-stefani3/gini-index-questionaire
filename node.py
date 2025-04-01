from typing import List, Optional
import pandas as pd
import numpy as np
from graphviz import Digraph


class Node:
    """Represents a single node in a decision tree with transition probability and cumulative scoring."""

    def __init__(self, question: str, column: str, parent_node: Optional["Node"] = None, score: float = 1.0):
        self.question = question
        self.column = column
        self.parent_node = parent_node
        self.score = score
        self.best_score: Optional[float] = score
        self.children: List["Node"] = []
        self.level: Optional[int] = None

        # Transition probability and cumulative scoring
        self.transition_probabilities = {}
        self.cumulative_score: Optional[float] = None
        self.normalized_cumulative_score: Optional[float] = None

    def add_children(self, children: List["Node"]):
        """Adds multiple child nodes."""
        self.children.extend(children)

    def update_best_scores(self, selection="min"):
        """Updating the best_score for each node in tree"""
        for child in self.children:
            child.update_best_scores(selection)

        # Compute the best score at this node
        self.best_score = self.score
        for child in self.children:
            if selection == "min":
                self.best_score = min(self.best_score, child.best_score)
            else:
                self.best_score = max(self.best_score, child.best_score)

    def max_height(self):
        """
        Calculate the maximum height of the n-ary tree.
        Height is the number of nodes along the longest path from self to leaf.

        Returns:
            int: Maximum height of the tree
        """

        # If no children, height is 1 (just this node)
        if not self.children:
            return 1

        # Recursively calculate height of each subtree and find maximum
        max_child_height = 0
        for child in self.children:
            child_height = child.max_height()  # Call max_height on child instance
            max_child_height = max(max_child_height, child_height)

        # Return max height of children plus 1 for current node
        return max_child_height + 1

    def assign_levels(self, max_height: int, depth: int = 1):
        """Assigns levels in reverse order based on depth."""
        self.level = max_height - depth + 1
        for child in self.children:
            child.assign_levels(max_height, depth + 1)

    def update_levels(self):
        max_height = self.max_height()
        self.assign_levels(max_height)

    def compute_scores(self, dataset: pd.DataFrame):
        """Computes transition probabilities, cumulative scores, and normalized cumulative scores in one traversal."""

        # Compute transition probabilities (Only applies to the current node)
        if self.children:
            parent_yes_count = (dataset[self.column] == 1.0).sum()
            for child in self.children:
                child_yes_given_parent_yes = ((dataset[self.column] == 1.0) & (dataset[child.column] == 1.0)).sum()
                self.transition_probabilities[child.column] = (
                    (child_yes_given_parent_yes / parent_yes_count) if parent_yes_count > 0 else 0
                )

        # Compute cumulative score recursively
        self.cumulative_score = self.score
        for child in self.children:
            child.compute_scores(dataset)
            self.cumulative_score += self.transition_probabilities.get(child.column, 0) * child.cumulative_score

        # Compute normalized cumulative score in the same pass
        self.normalized_cumulative_score = self.cumulative_score / self.level

    def update_all_nodes_with_cumulative(self, dataset: pd.DataFrame, selection="min"):
        """Computes transition probabilities, cumulative scores, and assigns levels."""
        max_height = self.max_height()
        self.assign_levels(max_height)
        self.update_best_scores(selection=selection)

        # # Compute transition probabilities and cumulative scores for each node
        self.compute_scores(dataset)

    def __repr__(self):
        return f"{self.column}___LEVEL={self.level}___IG={self.score}___CUM={self.cumulative_score}___NORM_CUM={self.normalized_cumulative_score})"

    def display(self):
        """Prints the tree structure in a hierarchical format."""

        def print_tree(node, prefix=""):
            """Recursively prints the tree with hierarchy formatting."""
            connector = "└──── " if node.parent_node and node == node.parent_node.children[-1] else "├──── "
            print(prefix + connector + str(node))

            for i, child in enumerate(node.children):
                extension = "      " if node.parent_node and node == node.parent_node.children[-1] else "│     "
                print_tree(child, prefix + extension)

        print_tree(self)

    def node_display(self, attribute):
        return f"{self.column}__IG={self.score:.3f}__CUM={self.cumulative_score:.3f}__NORM_CUM={getattr(self, attribute):.3f}"

    def to_graphviz(self, attribute, parent=None, graph=None):
        if graph is None:
            graph = Digraph(format="png")
            graph.attr(rankdir="LR")  # Set horizontal
            graph.node(self.node_display(attribute))

        if parent is not None:
            graph.edge(
                parent.node_display(attribute),
                self.node_display(attribute),
                label=f"TP={parent.transition_probabilities[self.column]:.3f}",
            )

        for child in self.children:
            child.to_graphviz(attribute=attribute, parent=self, graph=graph)

        return graph

    def visualize_tree(self, attribute, method):
        graph = self.to_graphviz(attribute=attribute)

        # Ensure output directory exists
        output_dir = f"generated_output/{method}"
        # os.makedirs(output_dir, exist_ok=True)

        # Render the graph
        graph.render(filename=f"{output_dir}/{self.column}", format="png", cleanup=True)

