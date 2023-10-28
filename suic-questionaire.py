import os

os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin'

from node import NODE
from helper import (
    load_json_file,
    get_cleaned_data,
    convert_scale_columns_to_classes,
    get_question_choices_data,
    get_utility_score,
    has_child,
    get_child_questions,
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
QUESTION_CHILD_MAPPER = load_json_file(BASE_PATH + "child_question_mapper.json")
ROOT_QUESTIONS = QUESTION_CHILD_MAPPER[DATASET_NAME]

"""
    making sure to add only columns which are
    available in QUESTION_MAPPER variable
    otherwise ignoring them
"""
QUESTION_QUEUE = []
for question in ROOT_QUESTIONS:
    if question in QUESTION_MAPPER:
        QUESTION_QUEUE.append(question)

# gets cleaned DataFrame from CSV File
dataset = get_cleaned_data(BASE_PATH, TARGET_COLUMN)

# converts all scale value columns into classes 'low', 'medium', 'high'
COMPLETE_DATASET = convert_scale_columns_to_classes(dataset, QUESTION_MAPPER)

# getting choices data for each column
CHOICES_DATASET = get_question_choices_data(COMPLETE_DATASET)

# Starting subset data with complete data then keep filtering out based on user answers
subset = COMPLETE_DATASET


def question_tree(question_queue):
    """
    question_queue: List of String(Questions)

    Final Output contain list of Root Level Question Tree
        [ Q1, Q2, Q3] -> where Q1, Q2 and Q3 represents Root Level Question Nodes which has chilren
        connected to them. Thus forming a Question Tree
    """

    """
        Bounding Function:
            If question_queue is empty then Return None
    """
    if len(question_queue) <= 0:
        return None

    # initializing output as empty list
    output = []

    # creating Node (Tree) for each Root Level Question
    for question in question_queue:
        # getting unique_choices for the current question
        unique_choices = CHOICES_DATASET.get(question)

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
            parent_node = NODE(question=question, score=1)
        else:
            """
            If there are values in unique_choices then
            we can calculate the score
            then create the Parent Node with the calculated score
            """
            score = get_utility_score(COMPLETE_DATASET, question, unique_choices, TARGET_COLUMN)
            parent_node = NODE(question=question, score=round(score, 3))

        # Add Child Question
        if has_child(question, QUESTION_CHILD_MAPPER):
            """
            If the question has child:
                child_questions -> then getting the child list
                child_branches -> Creating Child Nodes and Branches
                Then adding Child Branches/Nodes into the Parent Node

                Thus forming a Tree
            """
            child_questions = get_child_questions(question, QUESTION_CHILD_MAPPER)
            child_branches = question_tree(child_questions)
            parent_node.add_child_node(child_branches)

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
data = question_tree(QUESTION_QUEUE)

"""
    Printing the Tree in Human understandable Form
"""
for question in data:
    question.visualize_tree()

print("QUESTION TREES ARE SAVED INTO generated_output Folder")


def get_best_question_node_from_question_queue(question_queue):
    """
    question_queue -> List of Nodes

    Output -> Question Node (With Best Score)
    """
    # initialising Best Score and Best Node with None
    best_score = None
    best_node = None
    for question_node in question_queue:
        if best_score == None:
            """
            When best_score == None then first Node becomes best Score
            """
            best_score = question_node.best
            best_node = question_node
        elif question_node.best < best_score:
            """
            if find a better score then update
            best_score and
            best_node
            """
            best_score = question_node.best
            best_node = question_node

    # returning best node with best score
    return best_node


"""
    data is list of ROOT level Nodes

    question_queue is initialised with data.copy()
"""
question_queue = data.copy()

# initialising ordered_questions as empty list
ordered_questions = []

"""
    Running the loop till question_queue becomes empty 
"""
while question_queue:
    best_question_node = get_best_question_node_from_question_queue(question_queue)

    """
        Adding the best question into ordered_questions
    """
    ordered_questions.append(best_question_node.question)

    """
        If best question node has children then add them into question_queue
    """
    if best_question_node.children:
        question_queue.extend(best_question_node.children)

    """
        Removing Best Question Node from Question Queue
    """
    question_queue.remove(best_question_node)

print(f"Total Number of columns: {len(ordered_questions)}\n")
print("Top 15 Questions in Order of Importance")
for i, question in enumerate(ordered_questions[:15]):
    # printing questions in order of importance
    print(f"{i+1}) {question} - {QUESTION_MAPPER.get(question, {}).get('question', 'Unavailable')}\n")
