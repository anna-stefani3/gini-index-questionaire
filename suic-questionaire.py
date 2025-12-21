# import os
# os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin'
from pprint import pprint
import random
from node import Node
from helper import (
    load_json_file,
    get_cleaned_data,
    convert_scale_columns_to_classes,
    get_question_choices_data,
    get_information_gain,
    get_gini_score,
    has_child,
    get_child_questions,
    get_best_question_node_from_question_queue,
    get_previous_response,
)

### GLOBAL VARIABLES ###
# Defining Threshold values
MIN_SAMPLE_THRESHOLD = 100
DATASET_NAME = "suic_mg"
TARGET_COLUMN = "suic_mg"
BASE_PATH = ""

# getting question mapping for each column
QUESTION_MAPPER = load_json_file(BASE_PATH + "question-data.json")
BACKUP_QUESTION_MAPPER = load_json_file(BASE_PATH + "questions_mapping.json")

# getting child columns for each column
PARENT_CHILD_MAPPER = load_json_file(BASE_PATH + "child_question_mapper.json")
ROOT_QUESTIONS = PARENT_CHILD_MAPPER[DATASET_NAME]

"""
    making sure to add only columns which are
    available in QUESTION_MAPPER variable
    otherwise ignoring them
"""
QUESTION_QUEUE = ["suic_mg"]

# gets cleaned DataFrame from CSV File
dataset = get_cleaned_data(BASE_PATH, TARGET_COLUMN)

# converts all scale value columns into classes 'low', 'medium', 'high'
COMPLETE_DATASET = convert_scale_columns_to_classes(dataset, QUESTION_MAPPER)

# get all columns in dataset
DATASET_COLUMNS = COMPLETE_DATASET.columns

# getting choices data for each column
CHOICES_DATASET = get_question_choices_data(COMPLETE_DATASET)

# Starting subset data with complete data then keep filtering out based on user answers
subset = COMPLETE_DATASET


# Get the last row as a questionaire_response_history
questionaire_response_history = COMPLETE_DATASET.iloc[-1].to_dict()


def question_tree(column_queue, scoring_method="information_gain"):
    """
    column_queue: List of String(Questions)

    Final Output contain list of Root Level Question Tree
        [ Q1, Q2, Q3] -> where Q1, Q2 and Q3 represents Root Level Question Nodes which has chilren
        connected to them. Thus forming a Question Tree
    """

    """
        Bounding Function:
            If question_queue is empty then Return None
    """
    if len(column_queue) <= 0:
        return None

    # initializing output as empty list
    output = []

    # creating Node (Tree) for each Root Level Question
    for column in column_queue:
        # getting unique_choices for the current column
        unique_choices = CHOICES_DATASET.get(column)
        complete_question = QUESTION_MAPPER.get(column, {}).get("question")
        if not complete_question:
            continue

        previous_response = get_previous_response(questionaire_response_history, column)
        if previous_response is None or previous_response == -1:
            previous_response =  random.choice([0.0 , 1.0]) if unique_choices else -1
        previous_response = 1.0
        """
            unique_choices: represents the unique values available in CSV data
            there are many column which has complete N/A data example
        """
        if not unique_choices:
            """
            When uniques_choices is empty list
            NOTE: we can't calculate score without unique_choices
            Thats why creating Parent Node with worst score -> 1
            """
            # worst score is assigned according to scoring method
            score = 1.0 if scoring_method == "gini" else 0.0
            parent_node = Node(question=complete_question, column=column, parent_node=None, score=score, previous_response=previous_response)

        else:
            """
            If there are values in unique_choices then
            we can calculate the score
            then create the Parent Node with the calculated score
            """
            if scoring_method == "gini":
                score = get_gini_score(COMPLETE_DATASET, column, unique_choices, TARGET_COLUMN, previous_response)
            else:
                score = get_information_gain(COMPLETE_DATASET, column, unique_choices, TARGET_COLUMN, previous_response)
            parent_node = Node(question=complete_question, column=column, parent_node=None, score=round(score, 3), previous_response=previous_response)

        # Add Child Columns
        if has_child(column, PARENT_CHILD_MAPPER):
            """
            If the question has child:
                child_questions -> then getting the child list
                child_branches -> Creating Child Nodes and Branches
                Then adding Child Branches/Nodes into the Parent Node

                Thus forming a Tree
            """
            child_columns = get_child_questions(column, PARENT_CHILD_MAPPER, DATASET_COLUMNS)
            if child_columns:
                child_nodes = question_tree(child_columns, scoring_method)
                parent_node.add_children(child_nodes)

        """
            As each node in tree are initialized with None Value
            Calling update_best_scores to update the best score inside parent and all branch nodes
        """
        parent_node.update_best_scores()

        # adding Parent Node into the Output List
        output.append(parent_node)

    # Returning the final output of -> List of Root Level Questions
    return output


"""
    Calling question tree to create the tree using recursion

    Final Output contain list of Root Level Question Tree
        [ Q1, Q2, Q3] -> where Q1, Q2 and Q3 represents Root Level Question Nodes which has chilren
        connected to them. Thus forming a Question Tree
"""
question_tree_based_on_information_gain = question_tree(QUESTION_QUEUE, scoring_method="information_gain")
question_tree_based_on_gini_impurity = question_tree(QUESTION_QUEUE, scoring_method="gini")

global_counts = COMPLETE_DATASET[TARGET_COLUMN].value_counts().to_dict()

# updating all the score and cumulative score for information gain scoring method
question_tree_based_on_information_gain[0].update_all_nodes_with_cumulative(COMPLETE_DATASET, selection="max", target_column=TARGET_COLUMN, global_counts=global_counts)
question_tree_based_on_gini_impurity[0].update_all_nodes_with_cumulative(COMPLETE_DATASET, selection="min", target_column=TARGET_COLUMN, global_counts=global_counts)

# for child_node in question_tree_based_on_information_gain[0].children:
#     child_node.visualize_tree(attribute="normalized_cumulative_score", method="example")

"""
    data is list of ROOT level Nodes
    question_queue is initialised with data.copy()
"""


def get_ordered_question_list(question_queue, attribute="best_score", selection="min"):
    # initialising ordered_questions as empty list
    ordered_questions = []

    # Running the loop till question_queue becomes empty

    while question_queue:
        best_question_node = get_best_question_node_from_question_queue(question_queue, attribute, selection=selection)

        # Adding the best question into ordered_questions
        ordered_questions.append(best_question_node)

        # If best question node has children then add them into question_queue
        if best_question_node.children:
            question_queue.extend(best_question_node.children)

        # Removing Best Question Node from Question Queue
        question_queue.remove(best_question_node)
    return ordered_questions


information_gain_question_list = get_ordered_question_list(
    question_tree_based_on_information_gain, attribute="normalized_cumulative_score", selection="max"
)
gini_impurity_question_list = get_ordered_question_list(
    question_tree_based_on_gini_impurity, attribute="best_score", selection="min"
)


print(f"Total Column Count [Information Gain]: {len(information_gain_question_list)}")
print(f"Total Column Count [Gini Impurity   ]: {len(gini_impurity_question_list)}\n")
print("Top 15 Questions in Order of Importance")
for i in range(1, 16):
    information_gain = information_gain_question_list[i]
    gini_impurity = gini_impurity_question_list[i]
    # printing questions in order of importance
    information_gain_dict = {
        "question": information_gain.question,
        "risk_class": information_gain.risk_class,
        "risk_confidence": information_gain.final_risk_confidence,
        "answer": information_gain.previous_response,
    }
    gini_impurity_dict = {
        "question": gini_impurity.question,
        "risk_class": gini_impurity.risk_class,
        "risk_confidence": gini_impurity.final_risk_confidence,
        "answer": gini_impurity.previous_response,
    }
    print(i)
    print(f'{information_gain_dict["question"]}\n{information_gain_dict["answer"]} -> Risk Class: {information_gain_dict["risk_class"]}, Confidence: {information_gain_dict["risk_confidence"]}')
    print(f'{gini_impurity_dict["question"]}\n{gini_impurity_dict["answer"]} -> Risk Class: {gini_impurity_dict["risk_class"]}, Confidence: {gini_impurity_dict["risk_confidence"]}')
    print("\n\n")
