# import modules
from collections import Counter
import pandas as pd
import json
from pprint import pprint


# reading the question mapping data from json file
def load_json_file(filename):
    with open(filename) as file:
        data = json.load(file)
    return data


def get_cleaned_data():
    file_path = "Child/child-adolescent-hto.csv"
    # reading the csv file where we defined "\\N" as Missing Data
    data = pd.read_csv(file_path, na_values="\\N")

    data.rename(columns={"friends_peers_mg": "friends_colleagues_mg"}, inplace=True)
    # Getting Required Columns from dataset
    data = data.iloc[:, 4:]

    # droping all rows which has missing class (Risk Score)
    data = data.dropna(subset=["hto_mg"])

    # dropping rows where all the values are Missing Value
    data.dropna(how="all")

    # # replacing Missing Values with -1 constant number
    data = data.fillna(
        0
    )  # there are various other methods we can implement for imputing the missing data
    return data


### GLOBAL VARIABLES ###

# Defining Threshold values
MIN_SAMPLE_THRESHOLD = 100
GINI_PERCENTILE_THRESHOLD = 2


# getting question mapping for each column
QUESTION_MAPPER = load_json_file("question-data.json")
BACKUP_QUESTION_MAPPER = load_json_file("questions_mapping.json")

# getting child columns for each column
QUESTION_CHILD_MAPPER = load_json_file("child_question_mapper.json")

ROOT_QUESTIONS_FOR_HTO = QUESTION_CHILD_MAPPER["hto_mg"]

QUESTION_QUEUE = ROOT_QUESTIONS_FOR_HTO

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
def convert_scale_columns_to_classes(data):
    for column in data.columns:
        if QUESTION_MAPPER.get(column) and QUESTION_MAPPER[column]["values"] == "scale":
            data[column] = data[column].apply(convert_to_low_medium_and_high_risk)
    return data


# gets the choices for each column name for the user to answer
def get_question_choices_data(dataset):
    question_choices_data = {}
    for column in dataset.columns:
        unique_answers = list(dataset[column].unique())
        question_choices_data[column] = unique_answers

    return question_choices_data


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
def get_aggregated_gini_impurity(dataset, question, unique_answers):
    # initializing total_gini_score = 0
    total_gini_score = 0
    # Adding all Gini Scores for each uniques Answers for the given Question
    for answer in unique_answers:
        # selecting rows where question value == answer
        answer_df = dataset[dataset[question] == answer]

        # Getting labels for previously selected rows
        labels = answer_df["hto_mg"]

        # calculating Gini Impurity Score
        gini_impurity = gini_measure_of_impurity(list(labels.values))

        # Calculating answer likelihood
        answer_likelihood = len(labels.values) / dataset.shape[0]

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


def has_child(question):
    # returns if the specific question has child questions or not
    if QUESTION_CHILD_MAPPER[question]:
        return True
    else:
        return False


def get_sorted_scores_df(subset, choices_dataset):
    # initializing scores as empty list
    scores = []

    # adding scores for each question in the QUESTION_QUEUE
    for question in QUESTION_QUEUE:
        # getting Uniques Choices data from choices_dataset
        unique_choices = choices_dataset[question]

        # getting score data for specific question
        score = get_aggregated_gini_impurity(subset, question, unique_choices)

        # appending score into scores list
        scores.append(score)

    # converting to Dataframe
    scores_df = pd.DataFrame(scores)

    # sorting scores_df in Ascending Order
    sorted_scores_df = scores_df.sort_values(by="aggregated_gini", ascending=True)
    return sorted_scores_df


def get_rejected_question_list(scores_df, gini_threshold):
    # filtering from scores_df where score is greater than gini_threshold
    rejected_df = scores_df[scores_df["aggregated_gini"] > gini_threshold]

    # getting the names of the columns only from filtered data
    questions_list = list(rejected_df["question"])\
    
    # returning rejected questions List
    return questions_list


def remove_question(remove_list):
    # looping through each column name in remove_list
    for question in remove_list:
        # removing specific question from QUESTION_QUEUE
        QUESTION_QUEUE.remove(question)


def add_child_questions(question):
    """
    QUESTION_CHILD_MAPPER contains list of child question for a given question
    Data looks like this
    {
        "column_1" : ["column_10", "column_15", "column_21"],
        "column_2" : ["column_11", "column_18", "column_29", "column_51"],
        "column_3" : None
    }

    where None means there is no Child Question for "column_3"
    """
    # checking if column name exists in QUESTION_CHILD_MAPPER
    if QUESTION_CHILD_MAPPER.get(question):
        # if exists then fetch the child columns
        child_question = QUESTION_CHILD_MAPPER.get(question)

        # looping throught each column in the child list
        for question in child_question:
            # adding each child column into QUESTION_QUEUE
            QUESTION_QUEUE.insert(0, question)


if __name__ == "__main__":
    # reads the csv file and cleans it
    dataset = get_cleaned_data()

    # converts all scale value columns into classes 'low', 'medium', 'high'
    COMPLETE_DATASET = convert_scale_columns_to_classes(dataset)

    # getting choices data for each column
    CHOICES_DATASET = get_question_choices_data(dataset)

    # Starting subset data with complete data then keep filtering out based on user answers
    subset = COMPLETE_DATASET

    # used to maintain the user question and asnwer record
    QUESTION_ANSWER_RECORD = []

    # running while loop till the QUESTION_QUEUE is empty or
    # subset rows are less than MIN_SAMPLE_THRESHOLD
    while len(QUESTION_QUEUE) > 0 and subset.shape[0] > MIN_SAMPLE_THRESHOLD:
        # getting gini scores for the columns which are in QUESTION_QUEUE
        # sorted in ascending order
        scores_df = get_sorted_scores_df(subset, CHOICES_DATASET)

        # getting gini_threshold value based on GINI_PERCENTILE_THRESHOLD
        gini_threshold = (
            scores_df.iloc[0]["aggregated_gini"] * GINI_PERCENTILE_THRESHOLD
        )

        # getting columns names which needs to be removed as they don't
        # fulfil threshold criteria
        remove_list = get_rejected_question_list(scores_df, gini_threshold)

        # removing all columns which doesn't fullfil threshold criteria
        # from QUESTION_QUEUE
        remove_question(remove_list)

        # selecting the best question from Sorted scores_df
        select_question = scores_df.iloc[0]["question"]

        # removing select_question from the QUESTION_QUEUE
        QUESTION_QUEUE.remove(select_question)

        ## checking if select_question map is in QUESTION_MAPPER records
        if QUESTION_MAPPER.get(select_question):
            # getting question map from question-data.json records
            question = QUESTION_MAPPER[select_question]["question"]
        else:
            # in case there is no record found for the select_question then
            # getting question map from questions_mapping.json records
            question = BACKUP_QUESTION_MAPPER[select_question]

        # fetching all possible choices for the select_question
        choices = CHOICES_DATASET[select_question]

        # Asking user the question to get the user response as asnwer
        answer = input(
            f"""Please Answer : {question} ?\n""" f"""Choices are : {choices}\n"""
        )
        try:
            # if answer is float then covert to float type
            answer = float(answer)
        except:
            # if above code throws error means the answer is a string type
            answer = str(answer)
        if type(CHOICES_DATASET[select_question][0]) == str:
            # filtering data based on string value
            subset = subset[subset[select_question].str.contains(answer)]
        else:
            # filtering data based on float value
            subset = subset[subset[select_question] == answer]

        # this checks if selected question has child(descendent questions) or not
        if has_child(select_question):
            # if the answer is not 0(not "No")
            # then adding all the descendent questions to QUESTION_QUEUE
            if answer != 0:
                add_child_questions(select_question)

        # adding user response into QUESTION_ANSWER_RECORD
        QUESTION_ANSWER_RECORD.append(
            {"question": QUESTION_MAPPER[select_question]["question"], "answer": answer}
        )

    ## Printing the reason why the questionaire got stopped
    if len(QUESTION_QUEUE) == 0:
        print("QUESTIONAIRE ENDS CAUSE QUEUE IS NOW EMPTY")
    if subset.shape[0] < MIN_SAMPLE_THRESHOLD:
        print("QUESTIONAIRE ENDS CAUSE SUBSET SAMPLE IS LESS THAN MIN_SAMPLE_THRESHOLD")

    # printing the Recorded Question and answer for the user
    print("RECORDED QUESTION ANSWERS BELOW:")
    pprint(QUESTION_ANSWER_RECORD)

    # printing the risk associated to the answers given so far
    print("\n\n\nRisk associated data :\n")
    pprint(dict(Counter(list(subset["hto_mg"]))))
