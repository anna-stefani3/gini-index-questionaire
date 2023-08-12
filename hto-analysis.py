"""Algorithm for generating the question-choice data structure"""
import math
from collections import Counter
import pandas as pd
import json


# reading the question mapping data from json file
def get_question_mapping_data(filename):
    file = open(filename)
    data = json.load(file)
    file.close()
    return data


# Using JSON mapper to show actual Question Instead on Column Name when asking a question.
question_mapping = get_question_mapping_data("questions_mapping.json")

"""step 1.Require training-set"""

file_path = "Child/child-adolescent-hto.csv"
# reading the csv file where we defined "\\N" as Missing Data
data = pd.read_csv(file_path, na_values="\\N")

# Getting Required Columns from dataset
data = data.iloc[:, 4:]

# droping all rows which has missing class (Risk Score)
data = data.dropna(subset=["hto_mg"])

# dropping rows where all the values are Missing Value
data.dropna(how="all")

# # replacing Missing Values with -1 constant number
data = data.fillna(
    -1
)  # there are various other methods we can implement for imputing the missing data


def convert_to_low_medium_and_high_risk(label):
    if label < 0.4:
        return "low"
    elif label < 0.7:
        return "medium"
    else:
        return "high"


# getting Risk column
data["risk"] = data["hto_mg"].apply(convert_to_low_medium_and_high_risk)


"""Step 2. Require question-list ;; ((Q1 G(1)) (Qn G(n))) initially null scores"""


def calculate_entropy(class_list):
    class_counts = Counter(class_list)
    total_samples = len(class_list)
    
    entropy = 0
    for count in class_counts.values():
        probability = count / total_samples
        entropy -= probability * math.log2(probability)
    
    return entropy


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
        labels = answer_df["risk"]

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


def get_question_list(data):
    # initialising the questions list as an empty list (array)
    question_list = []
    for question in data.columns:
        # hto_mg and risk columns cant be used for getting aggregated gini scores
        # thats why they are ignored
        if question in ["hto_mg", "risk"]:
            continue
        unique_answers = list(data[question].unique())
        question_score = get_aggregated_gini_impurity(question, unique_answers, data)

        # adding response to the question_list array
        # question_list datatype = List of Dictionary
        question_list.append(question_score)
    return question_list


question_list = get_question_list(data)


"""Step 3. sort-questions in order of Gini score, high to low"""

# converting the question_list from LIST to DATAFRAME
question_list_df = pd.DataFrame(question_list)

# sorting question list in Descending Order
sorted_question_list_df = question_list_df.sort_values(
    by="aggregated_gini", ascending=True
)
print(sorted_question_list_df)

# Converting Sorted Question Dataframe to Array of JSON(List of Dict)
sorted_question_list = sorted_question_list_df.to_dict("records")

# print("\n\nTop 10 Sorted Question List Data")
# print(sorted_question_list_df.head(10))


""" 
Step 4. answer-questions := nil ;; empty list that will hold the 
given answers and associated question gini score
"""
question_answer_list = None


"""Step 5.min-sample ;; 100 x number-of-answers"""
min_sample = 100


""" Step 6. min-gini-change ;; change in gini from the previous answer """
min_gini_change = 0.001


""" 
Step 7.	score-questions (question-list answers training-set);; 
returns question list in order of scores, highest first.
"""


# this helps to find dataset with exactly same responses if there is any
def get_subset_data(data, question, answer):
    subset = data[data[question] == answer]
    return subset


def get_score_questions(
    data,
    sorted_question_list,
    min_sample,
    min_gini_change,
    gini_percentile_threshold,
    question_mapper,
):
    # appending useful columns for selecting columns for subset data
    # Nothing important in this
    filtered_questions = []

    # only to track the exactly same answer in the dataset
    # Nothing important in this
    subset = data

    # storing Question Scores along with Answer
    questions_scores = []

    # Calculating Gini Threshold based on the Percentile of Max Gini Score
    gini_threshold = (
        sorted_question_list[0]["aggregated_gini"] * gini_percentile_threshold
    )
    # making sure the question list is not empty
    if sorted_question_list is not None:
        for i in range(len(sorted_question_list)):
            # Checking if Question Score is above Gini Threshold
            if sorted_question_list[i]["aggregated_gini"] >= gini_threshold:
                # Checking Samples size is greater than min_sample * no. of Answers
                if (
                    data.shape[0] / sorted_question_list[i]["num_of_answers"]
                    >= min_sample
                ):
                    # getting Question
                    question = sorted_question_list[i]["question"]

                    # getting Aggregated Gini Score of  Question
                    current_gini = sorted_question_list[i]["aggregated_gini"]

                    # making sure index is not 0.
                    # as we can't compare difference between index 0 and index 0
                    if i != 0:
                        # getting gini change
                        # difference between gini score between current and previous Question
                        gini_change = (
                            sorted_question_list[i - 1]["aggregated_gini"]
                            - current_gini
                        )

                        # stores True or False based on gini_change is greater than threahold limit or not
                        greater_than_min_gini_change = gini_change >= min_gini_change
                    else:
                        # if index = 0, then we are going to select the question anyway
                        greater_than_min_gini_change = True

                    # If greater_than_min_gini_change is True then Question is Selected
                    if greater_than_min_gini_change:
                        # getting the possible choice for selected question based on dataset
                        answer_options = sorted_question_list[i]["answer_choices"]

                        # asking user to answer the question with choices given
                        answer = float(
                            input(
                                f"""Please Answer : {question_mapper[question]} ?\n"""
                                f"""Choices are : {answer_options}\n"""
                            )
                        )

                        # making sure user has answered the question correctly.
                        if answer in answer_options and answer is not None:
                            # getting Subset for exactly same answer
                            subset = get_subset_data(subset, question, answer)

                            # getting Gini Score for the given question and answer
                            labels = list(subset["risk"])
                            gini_score = gini_measure_of_impurity(labels)

                            # adding question and score into question-answer-score
                            questions_scores.append(
                                {
                                    "column": question,
                                    "question": question_mapper[question],
                                    "answer": answer,
                                    "gini_score": gini_score,
                                }
                            )
                            filtered_questions.append(question)
    filtered_questions.append("risk")

    # final Subset contains dataset with exactly same answers as given by user.(If Any)
    # this helps to visualize the risk labels
    subset = subset[filtered_questions]
    return questions_scores, subset


gini_percentile_threshold = 0.4

score_questions, subset = get_score_questions(
    data,
    sorted_question_list,
    min_sample,
    min_gini_change,
    gini_percentile_threshold,
    question_mapping,
)

import pprint

# printing the data in Table format for better and easy understanding
# pprint stands for pretty print which prettify the output printed.
pprint.pprint(score_questions, width=80)

# printing subset with exactly same answers (If any)
print(subset)
