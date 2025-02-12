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


def get_previous_response(questionaire_response_data: dict, question):
    return questionaire_response_data.get(question, None)


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


def get_utility_score(dataset, question, unique_answers, TARGET_COLUMN, prev_response=1, bias_factor=0.25):
    """
    Calculates the utility score based on the gini impurity and adjusted probability of answers.
    """
    total_utility_score = 0  # Initialize utility score
    weighted_probs = {}  # Dictionary to store weighted probabilities of answers

    # Count occurrences of each unique answer in the dataset
    answer_counts = {answer: (dataset[question] == answer).sum() for answer in unique_answers}

    # Adjust probabilities by applying bias towards the previous response
    for answer in unique_answers:
        if answer == prev_response:
            weight = 1 + bias_factor  # Increase weight for previous response
        else:
            weight = 1 - bias_factor  # Decrease weight for other responses
        weighted_probs[answer] = int(weight * answer_counts[answer])

    # Compute total weighted sum to normalize probabilities
    total_weighted_sum = sum(weighted_probs.values())

    # Compute adjusted probabilities for each answer
    adjusted_probabilities = {answer: weighted_probs[answer] / total_weighted_sum for answer in unique_answers}

    # Iterate through each unique answer to compute utility score
    for answer in unique_answers:
        answer_df = dataset[dataset[question] == answer]  # Filter dataset for current answer
        labels = answer_df[TARGET_COLUMN]  # Get target labels for current answer
        gini_impurity = gini_measure_of_impurity(list(labels.values))  # Calculate gini impurity

        # Use adjusted probability instead of uniform probability
        probability = adjusted_probabilities[answer]

        # Compute contribution of this answer to total utility score
        total_utility_score += gini_impurity * (1 - probability)

    # Compute the final average utility score
    average_score = total_utility_score / len(unique_answers)

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
