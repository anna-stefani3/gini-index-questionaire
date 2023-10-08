# import modules
from collections import Counter
import pandas as pd
import json
from pprint import pprint

from tree import TREE

### GLOBAL VARIABLES ###

# Defining Threshold values
MIN_SAMPLE_THRESHOLD = 100
DATASET_NAME = "suic_mg"


# reading the question mapping data from json file
def load_json_file(filename):
    with open(filename) as file:
        data = json.load(file)
    return data


def get_cleaned_data():
    file_path = "Child/child-adolescent-suic.csv"
    # reading the csv file where we defined "\\N" as Missing Data
    data = pd.read_csv(file_path, na_values="\\N")

    data.rename(columns={"friends_peers_mg": "friends_colleagues_mg"}, inplace=True)
    # Getting Required Columns from dataset
    data = data.iloc[:, 4:]

    # droping all rows which has missing class (Risk Score)
    data = data.dropna(subset=[DATASET_NAME])

    # dropping rows where all the values are Missing Value
    data.dropna(how="all")

    # # replacing Missing Values with 0 constant number which will represent
    # "NO" as an answer for that question
    data = data.fillna(0)  # there are various other methods we can implement for imputing the missing data
    return data


### GLOBAL VARIABLES ###

# getting question mapping for each column
QUESTION_MAPPER = load_json_file("question-data.json")
BACKUP_QUESTION_MAPPER = load_json_file("questions_mapping.json")

# getting child columns for each column
QUESTION_CHILD_MAPPER = load_json_file("child_question_mapper.json")

ROOT_QUESTIONS_FOR_HTO = QUESTION_CHILD_MAPPER[DATASET_NAME]

# making sure to add only columns which are
# available in QUESTION_MAPPER variable
# otherwise ignoring them
QUESTION_QUEUE = []
for question in ROOT_QUESTIONS_FOR_HTO:
    if question in QUESTION_MAPPER:
        QUESTION_QUEUE.append(question)


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
def get_utility_score(dataset, question, unique_answers):
    # initializing total_utility_score = 0
    total_utility_score = 0

    # Adding all Gini Scores for each uniques Answers for the given Question
    for answer in unique_answers:
        # selecting rows where question value == answer
        answer_df = dataset[dataset[question] == answer]

        # Getting labels for previously selected rows
        labels = answer_df[DATASET_NAME]

        # calculating Gini Impurity Score
        gini_impurity = gini_measure_of_impurity(list(labels.values))

        # Calculating probability
        probability = len(labels.values) / dataset.shape[0]

        # adding gini_impurity * (1 - probability) to total_utility_score

        """
        using (1 - probability) so that gini score with high probability can be
        multiplied with low number to increase the chances for that question to
        be selected

        as we want to reduce the score for high probability answers and vice versa

        as lower score means better question to be ask in gini score case
        """
        total_utility_score += gini_impurity * (1 - probability)

    # Aggregating or averaging the total_utility_score
    aggregated_score = total_utility_score / len(unique_answers)

    # returning required output followed as question, gini_score, num of answers, answer choice
    return {
        "question": question,
        "utility_score": aggregated_score,
        "num_of_answers": len(unique_answers),
        "answer_choices": unique_answers,
    }


def has_child(question):
    # returns if the specific question has child questions or not
    # returns only TRUE or FALSE
    if QUESTION_CHILD_MAPPER[question]:
        return True
    else:
        return False


def get_sorted_utility_scores_df(complete_dataset, choices_dataset):
    # initializing scores as empty list
    scores = []

    # adding scores for each question in the QUESTION_QUEUE
    for question in QUESTION_QUEUE:
        if question in choices_dataset:
            # getting Uniques Choices data from choices_dataset
            unique_choices = choices_dataset[question]

            # getting score data for specific question
            score = get_utility_score(complete_dataset, question, unique_choices)

            # appending score into scores list
            scores.append(score)

    # converting to Dataframe
    scores_df = pd.DataFrame(scores)

    # sorting scores_df in Ascending Order
    sorted_scores_df = scores_df.sort_values(by="utility_score", ascending=True)
    return sorted_scores_df


def get_rejected_question_list(scores_df, gini_threshold):
    # filtering from scores_df where score is greater than gini_threshold
    rejected_df = scores_df[scores_df["utility_score"] > gini_threshold]

    # getting the names of the columns only from filtered data
    questions_list = list(rejected_df["question"])
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
            # if child column exist in QUESTION_MAPPER
            if QUESTION_MAPPER.get(question):
                # adding each child column into QUESTION_QUEUE
                QUESTION_QUEUE.insert(0, question)


def get_output(question, subset):
    pass


def minimax(QUESTION_QUEUE, subset, output):
    if len(QUESTION_QUEUE) <= 0 or subset.shape[0] <= MIN_SAMPLE_THRESHOLD:
        return output

    for question in QUESTION_QUEUE:
        output[question] = None


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
        scores_df = get_sorted_utility_scores_df(COMPLETE_DATASET, CHOICES_DATASET)
        print(scores_df)

        # selecting the best question from Sorted scores_df
        selected_question = scores_df.iloc[0]["question"]

        # removing selected_question from the QUESTION_QUEUE
        QUESTION_QUEUE.remove(selected_question)

        ## checking if selected_question map is in QUESTION_MAPPER records
        if QUESTION_MAPPER.get(selected_question):
            # getting question map from question-data.json records
            question = QUESTION_MAPPER[selected_question]["question"]
        else:
            # in case there is no record found for the selected_question then
            # getting question map from questions_mapping.json records
            question = BACKUP_QUESTION_MAPPER[selected_question]

        # fetching all possible choices for the selected_question
        choices = CHOICES_DATASET[selected_question]

        # Asking user the question to get the user response as asnwer
        answer = input(f"""Please Answer : {question} ?\nChoices are : {choices}\n""")
        try:
            # if answer is float then covert to float type
            answer = float(answer)
        except:
            # if above code throws error means the answer is a string type
            answer = str(answer)
        if type(CHOICES_DATASET[selected_question][0]) == str:
            # filtering data based on string value
            subset = subset[subset[selected_question].str.contains(answer)]
        else:
            # filtering data based on float value
            subset = subset[subset[selected_question] == answer]

        # this checks if selected question has child(descendent questions) or not
        if has_child(selected_question):
            # if the answer is not 0(not "No")
            # then adding all the descendent questions to QUESTION_QUEUE
            if answer != 0:
                add_child_questions(selected_question)

        # adding user response into QUESTION_ANSWER_RECORD
        QUESTION_ANSWER_RECORD.append({"question": QUESTION_MAPPER[selected_question]["question"], "answer": answer})

    ## Printing the reason why the questionaire got stopped
    if len(QUESTION_QUEUE) == 0:
        print("QUESTIONAIRE ENDS CAUSE QUEUE IS NOW EMPTY")
    if subset.shape[0] < MIN_SAMPLE_THRESHOLD:
        print("QUESTIONAIRE ENDS CAUSE SUBSET SAMPLE IS LESS THAN MIN_SAMPLE_THRESHOLD")

    # printing the Recorded Question and answer for the user
    print("RECORDED QUESTION ANSWERS BELOW:")
    pprint(QUESTION_ANSWER_RECORD)

    ##  **********       PRINTING PROBABLE RISK       **********

    # getting count for subset data
    subset_counter = dict(Counter(list(subset[DATASET_NAME])))

    # getting count for complete data
    full_data_counter = dict(Counter(list(COMPLETE_DATASET[DATASET_NAME])))

    # initialising final risk data
    risk_data = {}
    highest_risk = 0
    for risk_class in full_data_counter:
        # if risk_class in subset_counter
        if risk_class in subset_counter:
            # calculating risk based on probability of occurance of the risk class
            # rounding the score till 2 decimal place

            """
            inversing the probability for risk_class
            so that risk_class with less occurance in dataset
            can be multiplied by higher number


            example Suppose there are 100 rows with "high" risk in complete dataset
            and there are 10000 rows in complete_dataset
            so probability_of_high = rows with "high" / length_of_complete_dataset
                                    = 100 / 10000
                                    = 0.01


            risk = subset_counter["high"] * (1 - probability_of_high) = subset_counter["high"] * 0.9


            this is basically done to account for imbalance in risk class
            """
            normalised_risk = round(
                subset_counter[risk_class] * (1 - full_data_counter[risk_class] / COMPLETE_DATASET.shape[0]),
                2,
            )
            risk_data[risk_class] = normalised_risk
            if normalised_risk > highest_risk:
                highest_risk = normalised_risk
        else:
            risk_data[risk_class] = 0
    if risk_data["low"] == highest_risk and risk_data["medium"] + risk_data["high"] > risk_data["low"]:
        final_risk = "medium"
    elif risk_data["high"] == highest_risk:
        final_risk = "high"
    elif risk_data["medium"] == highest_risk:
        final_risk = "medium"
    else:
        final_risk = "low"

    print("\n\n\nRISK IS PROBABLY :", final_risk)
