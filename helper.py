import pandas as pd
import json


# reading the question mapping data from json file
def load_json_file(filename):
    with open(filename) as file:
        data = json.load(file)
    return data


def get_cleaned_data(base_path, target_column):
    """
        base_path: String -> base path for code and csv files
        target_column: String -> contains the name of the target column in csv dataset

        output is cleaned DataFrame where NA is replace with -1 value

    """
    file_path = "Child/child-adolescent-suic.csv"
    # reading the csv file where we defined "\\N" as Missing Data
    data = pd.read_csv(base_path + file_path, na_values="\\N")

    data.rename(columns={"friends_peers_mg": "friends_colleagues_mg"}, inplace=True)
    # Getting Required Columns from dataset
    data = data.iloc[:, 4:]

    # droping all rows which has missing class (Risk Score)
    data = data.dropna(subset=[target_column])

    # dropping rows where all the values are Missing Value
    data.dropna(how="all")

    # # replacing Missing Values with -1 constant number which will represent
    # "NO" as an answer for that question
    data = data.fillna(-1)  # there are various other methods we can implement for imputing the missing data
    return data


### UTIL FUNCTIONS ###
# converts the scale data into classes "low", "medium", "high"
def convert_to_low_medium_and_high_risk(label):
    """
        low -> 0 to 0.3
        medium -> 0.4 to 0.6
        high -> 0.7 to 1.0
    """
    if label < 0.4:
        return "low"
    elif label < 0.7:
        return "medium"
    else:
        return "high"


# converts all scale columns to class data
def convert_scale_columns_to_classes(data, QUESTION_MAPPER):
    """
        Scale values columns (columns which contains values 0, 0.1, 0.2, 0.3 ........ 0.9, 1.0)
        are converted to 'low', 'medium' and 'high' accordingly
    """
    for column in data.columns:
        if QUESTION_MAPPER.get(column) and QUESTION_MAPPER[column]["values"] == "scale":
            data[column] = data[column].apply(convert_to_low_medium_and_high_risk)
    return data


# gets the choices for each column name for the user to answer
def get_question_choices_data(dataset):
    """
        generates the possible choices for given column names

        Example Output is dictionary ->
        key is a the column name and value is the list of all possible answers(choices).

        {
            "question 1" : [0 , 1],
            "question 2" : [0 , 1],
            "question 3" : [0 , 1],
            "question 4" : ['low, 'medium', 'high']
        }
    """
    question_choices_data = {}
    for column in dataset.columns:
        # gets the unique answers list
        unique_answers = list(dataset[column].unique())

        # removing -1 from uniques_answers list
        unique_answers = [answer for answer in unique_answers if answer != -1]

        # adding the choices for respective question into the dictionary
        question_choices_data[column] = unique_answers

    # returns Dictionary
    return question_choices_data


# Calculated Gini Impurity for given List of Risk Labels
def gini_measure_of_impurity(labels):
    """
        labels : list of string
        example -> ['low', 'low', 'high', 'low', 'low', 'low', 'low', 'medium' ]

        OUTPUT:
        gini impurity score. this score ranges from 0 to 1.
        Where 0 represent the best score and 1 represents the worst score
    """
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
def get_utility_score(dataset, question, unique_answers, TARGET_COLUMN):
    """
        Initializes Utility Score with 0

        For each unique answer for question:
            1. getting target label or rows where [column value == answer]
            2. calculating gini_score using the labels
            3. calculating probability of that answer being being chosen
            4. adding gini_impurity * (1 - probability) into utility score

        gettting average_utility_score

        returning average_utility_score
    """
    # initializing total_utility_score = 0
    total_utility_score = 0

    # Adding all Gini Scores for each uniques Answers for the given Question
    for answer in unique_answers:
        # selecting rows where question value == answer
        answer_df = dataset[dataset[question] == answer]

        # Getting labels for previously selected rows
        labels = answer_df[TARGET_COLUMN]

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
    average_score = total_utility_score / len(unique_answers)

    # returning required output followed as question, gini_score, num of answers, answer choice
    return average_score


def has_child(question, QUESTION_CHILD_MAPPER):
    """
        checks if a given question has child or not

        Return Either True or False
    """
    if QUESTION_CHILD_MAPPER.get(question):
        return True
    else:
        return False


def get_child_questions(question, QUESTION_CHILD_MAPPER):
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
        return QUESTION_CHILD_MAPPER.get(question)
    return None
