from typing import List, Optional
import pandas as pd
import numpy as np
# from graphviz import Digraph


class Node:
    """Represents a single node in a decision tree with transition probability and cumulative scoring."""

    def __init__(self, question: str, column: str, parent_node: Optional["Node"] = None, score: float = 1.0, previous_response: Optional[str] = None):
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

        # NEW: risk info for this question
        self.previous_response: Optional[str] = previous_response
        self.current_risk_distribution: tuple = ()
        self.accumulated_risk_distribution: tuple = ()
        self.risk_distribution: dict = {}
        self.risk_class: Optional[str] = None
        self.risk_confidence: Optional[float] = 0.0
        self.final_risk_confidence: Optional[float] = 0.0

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

    def compute_scores(self, dataset: pd.DataFrame, target_column: str, global_counts: dict=None):
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
            child.compute_scores(dataset, target_column, global_counts)
            self.cumulative_score += self.transition_probabilities.get(child.column, 0) * child.cumulative_score

        # Compute normalized cumulative score in the same pass
        self.normalized_cumulative_score = self.cumulative_score / self.level

        # Compute risk distribution & dominant risk class using self.column as the target
        if self.column in dataset.columns:
            if self.previous_response is not None and self.previous_response != -1:
                rows = dataset[dataset[self.column] == self.previous_response]
            else:
                rows = dataset[dataset[self.column] != -1]
            percentage_counts = rows[target_column].value_counts(normalize=True).reindex(('low', 'medium', 'high'), fill_value=0).to_dict()
            abs_counts = rows[target_column].value_counts().reindex(['low', 'medium', 'high'], fill_value=0).to_dict()
            # sum as float
            ratios = {}
            for risk_class in ('low', 'medium', 'high'):
                risk_class_count = global_counts.get(risk_class, 1)
                ratios[risk_class] = (abs_counts.get(risk_class, 0) / risk_class_count)
            total = float(sum(ratios.values()))

            # normalize so values sum to 1 (handle total == 0)
            if total > 0:
                normalized_percentage_counts = {risk_class: round(ratios[risk_class] / total, 2) for risk_class in ratios}
            else:
                normalized_percentage_counts = {risk_class: round(ratios[risk_class], 2) for risk_class in ratios}

            self.current_risk_distribution = normalized_percentage_counts
            self.risk_distribution = normalized_percentage_counts
            self.set_accumulated_risk_distribution()
            self.risk_class = max(self.accumulated_risk_distribution, key=self.accumulated_risk_distribution.get) if self.accumulated_risk_distribution else None
            self.risk_confidence = max(self.accumulated_risk_distribution.values()) if self.accumulated_risk_distribution else 0.0
            self.final_risk_confidence = round(self.risk_confidence ** 0.4, 2)
        else:
            self.current_risk_distribution = {"low": 0.0, "medium": 0.0, "high": 0.0}
            self.accumulated_risk_distribution = {"low": 0.0, "medium": 0.0, "high": 0.0}
            self.risk_class = "low"
            self.risk_confidence = 0.0
            self.final_risk_confidence = 0.0
        
    def set_accumulated_risk_distribution(self):
        """Computes accumulated risk distribution from current node and its children."""
        
        """
        Idea is to calculate the sum/2 for each class separately to get accumulated risk distribution
        sum needs to be performed between current_risk_distribution and parent's accumulated_risk_distribution
        In case there is no parent node then current_risk_distribution is the accumulated_risk_distribution
        """
        if not self.parent_node:
            self.accumulated_risk_distribution = self.current_risk_distribution
        else:
            accumulated = {}
            for key in set(self.current_risk_distribution.keys()).union(set(self.parent_node.accumulated_risk_distribution.keys())):
                accumulated[key] = (
                    self.current_risk_distribution.get(key, 0) + self.parent_node.accumulated_risk_distribution.get(key, 0)
                ) / 2
            self.accumulated_risk_distribution = accumulated

    # update signature to accept target_column and pass it through
    def update_all_nodes_with_cumulative(self, dataset: pd.DataFrame, target_column: str, selection="min", global_counts=None):
        """Computes transition probabilities, cumulative scores, and assigns levels."""
        max_height = self.max_height()
        self.assign_levels(max_height)
        self.update_best_scores(selection=selection)

        # # Compute transition probabilities and cumulative scores for each node
        self.compute_scores(dataset, target_column, global_counts)

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

    # def to_graphviz(self, attribute, parent=None, graph=None):
    #     if graph is None:
    #         graph = Digraph(format="png")
    #         graph.attr(rankdir="LR")  # Set horizontal
    #         graph.node(self.node_display(attribute))

    #     if parent is not None:
    #         graph.edge(
    #             parent.node_display(attribute),
    #             self.node_display(attribute),
    #             label=f"TP={parent.transition_probabilities[self.column]:.3f}",
    #         )

    #     for child in self.children:
    #         child.to_graphviz(attribute=attribute, parent=self, graph=graph)

    #     return graph

    # def visualize_tree(self, attribute, method):
    #     graph = self.to_graphviz(attribute=attribute)

    #     # Ensure output directory exists
    #     output_dir = f"generated_output/{method}"
    #     # os.makedirs(output_dir, exist_ok=True)

    #     # Render the graph
    #     graph.render(filename=f"{output_dir}/{self.column}", format="png", cleanup=True)

