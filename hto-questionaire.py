# import modules

import math
from collections import Counter
import pandas as pd
import json
from pprint import pprint


# reading the question mapping data from json file
def load_json_file(filename):
    with open(filename) as file:
        data = json.load(file)
    return data

### GLOBAL VARIABLES ###
# getting question mapping for each column
question_mapping = load_json_file("question-data.json")

# getting child columns for each column
child_question_mapper = load_json_file("child_question_mapper.json")


### UTIL FUNCTIONS ###

# converts the scale data into classes "low", "medium", "high"
def convert_to_low_medium_and_high_risk(label):
    if label < 0.4:
        return "low"
    elif label < 0.7:
        return "medium"
    else:
        return "high"


# converts all scale columns to class data
def convert_scale_columns_to_classes(data, question_mapping):
    for column in data.columns:
        if question_mapping[column]["values"] == "scale":
            data[column] = data[column].apply(convert_to_low_medium_and_high_risk)
    return data

# Calculated Gini Impurity for given List of Risk Labels
def gini_measure_of_impurity(labels):
    total_count = len(labels)
    if total_count == 0:
        return 0
    impurity = 1
    unique_labels = set(labels)

    # Here Labels Represent "high", "medium" and "low" Risk Label
    # Thus Calculating the Gini Impurity based on Label
    for label in unique_labels:
        label_count = labels.count(label)
        label_prob = label_count / total_count
        impurity -= label_prob**2
    return impurity


# Aggregating the Gini Scores for a Given Question
def get_aggregated_gini_impurity(question, unique_answers, df):
    # initializing total_gini_score = 0
    total_gini_score = 0

    # Adding all Gini Scores for each uniques Answers for the given Question
    for answer in unique_answers:
        # selecting rows where question value == answer
        answer_df = df[df[question] == answer]

        # Getting labels for previously selected rows
        labels = answer_df["hto_mg"]

        # calculating Gini Impurity Score
        gini_impurity = gini_measure_of_impurity(list(labels.values))

        # Calculating answer likelihood
        answer_likelihood = len(labels.values) / df.shape[0]

        # adding gini_impurity * answer_likelihood to total_gini_score
        total_gini_score += gini_impurity * answer_likelihood

    # Aggregating the gini score
    aggregated_score = total_gini_score / len(unique_answers)

    # returning required output followed as question, gini_score, num of answers, answer choice
    return {
        "question": question,
        "aggregated_gini": aggregated_score,
        "num_of_answers": len(unique_answers),
        "answer_choices": unique_answers,
    }