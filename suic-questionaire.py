from tree import TREE
from helper import (
    load_json_file,
    get_cleaned_data,
    convert_scale_columns_to_classes,
    get_question_choices_data,
    get_utility_score,
    has_child,
    add_child_questions,
)

### GLOBAL VARIABLES ###
# Defining Threshold values
MIN_SAMPLE_THRESHOLD = 100
DATASET_NAME = "suic_mg"
BASE_PATH = ""

# getting question mapping for each column
QUESTION_MAPPER = load_json_file(BASE_PATH + "question-data.json")
BACKUP_QUESTION_MAPPER = load_json_file(BASE_PATH + "questions_mapping.json")

# getting child columns for each column
QUESTION_CHILD_MAPPER = load_json_file(BASE_PATH + "child_question_mapper.json")
ROOT_QUESTIONS = QUESTION_CHILD_MAPPER[DATASET_NAME]

# making sure to add only columns which are
# available in QUESTION_MAPPER variable
# otherwise ignoring them
QUESTION_QUEUE = []
for question in ROOT_QUESTIONS:
    if question in QUESTION_MAPPER:
        QUESTION_QUEUE.append(question)

# gets cleaned DataFrame from CSV File
dataset = get_cleaned_data(BASE_PATH, DATASET_NAME)

# converts all scale value columns into classes 'low', 'medium', 'high'
COMPLETE_DATASET = convert_scale_columns_to_classes(dataset, QUESTION_MAPPER)

# getting choices data for each column
CHOICES_DATASET = get_question_choices_data(dataset)

# Starting subset data with complete data then keep filtering out based on user answers
subset = COMPLETE_DATASET


def question_recursion(question_queue, depth=4, ASKED_QUESTION=[], level=0):
    question_queue = [question for question in question_queue if question not in ASKED_QUESTION]

    # question_queue is empty of subset is less that MIN_SAMPLE_THRESHOLD then return None
    if len(question_queue) <= 0 or subset.shape[0] < MIN_SAMPLE_THRESHOLD:
        return None
    # if level is more than depth size then return None
    elif level > depth:
        return None
    output = []
    for question in question_queue:
        queue = [question]
        asked_question = ASKED_QUESTION.copy()
        if question not in asked_question:
            queue.remove(question)

            asked_question.append(question)
            unique_choices = CHOICES_DATASET.get(question)

            if not unique_choices:
                continue

            # getting score data for specific question
            score = get_utility_score(COMPLETE_DATASET, question, unique_choices, DATASET_NAME)
            root = TREE(question, unique_choices, round(score["utility_score"], 3), queue, level)

            # Add Child Question
            if has_child(question, QUESTION_CHILD_MAPPER):
                queue = add_child_questions(question, queue, QUESTION_MAPPER, QUESTION_CHILD_MAPPER)

            # going to next Level node
            node = question_recursion(queue, depth, asked_question, level + 1)
            if node:
                root.add_child_node(node)
            output.append(root)
    return output


# depth can be changed and played around like 3 or 4 or 5 or 6 and so on
data = question_recursion(QUESTION_QUEUE, depth=4)

# printing the tree Like structure of the Questionaire Simulation via recursion
for question in data:
    question.print_()

# printing best scores for the Root Questions using Tree
for question in data:
    best = question.get_best_score()
    print(question.question, best)
