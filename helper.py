import pandas as pd
import numpy as np
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


def calculate_entropy(labels):
    """
    Calculate the entropy of a list of class labels.

    Entropy is a measure from information theory that quantifies the uncertainty or impurity in a dataset.
    In the context of machine learning, it helps determine how mixed the class labels are.
    A lower entropy indicates a purer dataset, while a higher entropy indicates more disorder.

    Parameters:
    - labels: list of str
        A list containing class labels.
        Example: ['low', 'low', 'high', 'low', 'low', 'low', 'low', 'medium']

    Returns:
    - float
        The entropy value, ranging from 0 (pure, all elements are of the same class) to log2(n_classes)
        (maximum impurity, elements are evenly distributed among classes).
    """
    # Calculate the total number of labels
    total_count = len(labels)

    # If there are no labels, the entropy is 0 because there's no uncertainty
    if total_count == 0:
        return 0

    # Use numpy's unique function to find unique labels and their respective counts
    _, counts = np.unique(labels, return_counts=True)

    # Calculate the probability of each unique label
    probabilities = counts / total_count

    # Compute the entropy using the formula: -sum(p * log2(p)) for each unique label
    entropy_value = -np.sum(probabilities * np.log2(probabilities))

    return entropy_value


def calculate_gini_impurity(labels):
    """
    Calculate the Gini impurity for a list of class labels.

    Gini impurity measures the probability of incorrectly classifying a randomly chosen element
    from the set if it was labeled according to the distribution of labels in the subset.
    It ranges from 0 (pure, all elements are of the same class) to 1 (impure, elements are
    evenly distributed among classes).

    Parameters:
    - labels: list of str
        A list of class labels.
        Example: ['low', 'low', 'high', 'low', 'low', 'low', 'low', 'medium']

    Returns:
    - float
        Gini impurity score ranging from 0 (best, pure) to 1 (worst, impure).
    """
    # Total number of elements in the list
    total_count = len(labels)

    # If the list is empty, return 0 as the impurity
    if total_count == 0:
        return 0

    # Initialize impurity to 1 (maximum impurity)
    impurity = 1

    # Create a set of unique class labels from the input list
    unique_labels = set(labels)

    # Iterate over each unique label to calculate its probability
    for label in unique_labels:
        # Count how many times the current label appears in the list
        label_count = labels.count(label)

        # Calculate the probability of this label
        label_prob = label_count / total_count

        # Subtract the squared probability from the impurity
        impurity -= label_prob**2

    # Return the final Gini impurity score
    return impurity


def get_normalised_weights(dataset, question, unique_answers, prev_response, bias_factor=0.25):
    """
    Calculate normalized weights for each unique answer to a given question in the dataset,
    applying a bias towards a previous response if provided.

    Parameters:
    - dataset: pandas.DataFrame
        The dataset containing the data to be analyzed.
    - question: str
        The column name in the dataset representing the feature (question) of interest.
    - unique_answers: list
        A list of all possible unique values (answers) for the specified question.
    - prev_response: str or None
        The previous answer given, used to apply a bias. If None, no bias is applied.
    - bias_factor: float, optional (default=0.25)
        The factor by which to increase or decrease the weight of the previous response.
        A higher value increases the influence of the previous response.

    Returns:
    - normalised_weights: dict
        A dictionary where keys are unique answers and values are their corresponding normalized weights.
    """
    # Initialize a dictionary to store the weighted counts of each answer
    weighted_counts = {}

    # Iterate over each unique answer to calculate its weighted count
    for answer in unique_answers:
        # Count how many times the current answer appears in the dataset for the specified question
        count = (dataset[question] == answer).sum()

        # Determine the weight to apply:
        # - If the answer matches the previous response, increase its weight by the bias factor.
        # - Otherwise, decrease its weight by the bias factor.
        if answer == prev_response:
            weight = 1 + bias_factor  # Increase weight for the previous response
        else:
            weight = 1 - bias_factor  # Decrease weight for other responses

        # Calculate the weighted count for the current answer
        weighted_count = weight * count

        # Store the weighted count in the dictionary
        weighted_counts[answer] = weighted_count

    # Calculate the total of all weighted counts to use for normalization
    total_weighted_count = sum(weighted_counts.values())

    # Initialize a dictionary to store the normalized weights
    normalised_weights = {}

    # Iterate over each unique answer to calculate its normalized weight
    for answer in unique_answers:
        # Avoid division by zero by checking if the total weighted count is greater than zero
        if total_weighted_count > 0:
            # Calculate the normalized weight as the weighted count divided by the total weighted count
            normalized_weight = weighted_counts[answer] / total_weighted_count
        else:
            # If the total weighted count is zero, assign a normalized weight of zero
            normalized_weight = 0

        # Store the normalized weight in the dictionary
        normalised_weights[answer] = normalized_weight

    # Return the dictionary containing normalized weights for each unique answer
    return normalised_weights


def get_gini_score(dataset, question, unique_answers, target_column, prev_response=None):
    """
    Calculate the average Gini impurity score for a given feature (question) in the dataset.

    Gini impurity measures the likelihood of incorrectly classifying a randomly chosen element
    from the dataset if it was labeled according to the distribution of labels in the subset.
    This function evaluates how well a particular feature separates the data concerning the target variable.

    Parameters:
    - dataset: pandas.DataFrame
        The dataset containing the data to be analyzed.
    - question: str
        The column name in the dataset representing the feature to evaluate.
    - unique_answers: list
        A list of all possible unique values (answers) for the specified feature.
    - target_column: str
        The column name representing the target variable (the outcome or label).
    - prev_response: str, optional
        The previous answer given, used to adjust weights if applicable (default is None).

    Returns:
    - average_score: float
        The average Gini impurity score across all unique answers for the specified feature.
    """
    # Initialize the total utility score to accumulate the weighted Gini impurities
    total_utility_score = 0

    # Obtain normalized weights for each unique answer, potentially adjusted based on previous responses
    normalised_weights = get_normalised_weights(dataset, question, unique_answers, prev_response)

    # Iterate over each unique answer to calculate its contribution to the total utility score
    for answer in unique_answers:
        # Filter the dataset to include only rows where the feature (question) matches the current answer
        answer_df = dataset[dataset[question] == answer]

        # Extract the target variable values (labels) for the filtered subset
        labels = answer_df[target_column]

        # Calculate the Gini impurity for the current subset of labels
        gini_impurity = calculate_gini_impurity(list(labels.values))

        # Retrieve the normalized weight for the current answer; default to 0 if not found
        probability = normalised_weights.get(answer, 0)

        # Adjust the Gini impurity by the complement of the probability (1 - probability)
        # This reflects the weighted contribution of the current subset to the total impurity
        total_utility_score += gini_impurity * (1 - probability)

    # Calculate the average Gini impurity score by dividing the total utility score
    # by the number of unique answers. This provides a normalized measure of impurity
    # across all possible answers for the feature.
    average_score = total_utility_score / len(unique_answers)

    # Return the computed average Gini impurity score
    return average_score


def get_information_gain(dataset, question, unique_answers, target_column, prev_response=None):
    """
    Calculate the Information Gain for a specific question (feature) in a dataset.

    Information Gain measures how much knowing the value of a feature reduces uncertainty about the target variable. It's a key concept in building decision trees, helping to determine which feature to split on at each step.

    Parameters:
    - dataset: pandas.DataFrame
        The dataset containing all the data.
    - question: str
        The column name in the dataset representing the feature (question) we're evaluating.
    - unique_answers: list
        A list of all possible unique values (answers) for the feature in question.
    - target_column: str
        The column name in the dataset representing the target variable (what we're trying to predict).
    - prev_response: (Optional) str
        The previous answer given, used to adjust weights if applicable.

    Returns:
    - information_gain: float
        The calculated Information Gain for the specified feature.
    """
    # Step 1: Calculate normalized weights for each unique answer.
    # These weights represent the adjusted probabilities of each answer, potentially modified by prior responses.
    normalised_weights = get_normalised_weights(dataset, question, unique_answers, prev_response)

    # Step 2: Filter the dataset to include only rows where the feature's value is in unique_answers.
    # This ensures we're focusing on relevant data for our calculations.
    parent_df = dataset[dataset[question].isin(unique_answers)]

    # Step 3: Extract the target variable values from the filtered dataset.
    # These are the actual outcomes we're interested in predicting.
    parent_labels = parent_df[target_column]

    # Step 4: Calculate the entropy before any splitting.
    # Entropy quantifies the uncertainty or impurity in the target variable.
    # A higher entropy indicates more disorder, while a lower entropy indicates more order.
    entropy_before_split = calculate_entropy(list(parent_labels.values))

    # Initialize a variable to accumulate the entropy after splitting based on the feature.
    entropy_after_split = 0

    # Step 5: Iterate over each unique answer to evaluate how it affects the target variable's entropy.
    for answer in unique_answers:
        # a. Create a subset of the dataset where the feature equals the current answer.
        answer_df = dataset[dataset[question] == answer]

        # b. Extract the target variable values for this subset.
        labels = answer_df[target_column]

        # c. Calculate the entropy for this subset.
        split_entropy = calculate_entropy(list(labels.values))

        # d. Retrieve the normalized weight for the current answer.
        # This weight reflects the adjusted probability of encountering this answer.
        weight = normalised_weights.get(answer, 0)

        # e. Accumulate the weighted entropy.
        # By multiplying the subset's entropy by its weight, we account for its proportionate impact.
        entropy_after_split += split_entropy * weight

    # Step 6: Compute the Information Gain.
    # This is done by subtracting the weighted post-split entropy from the pre-split entropy.
    # A higher Information Gain indicates that the feature provides significant information about the target variable.
    information_gain = entropy_before_split - entropy_after_split

    return information_gain


def has_child(question, QUESTION_CHILD_MAPPER):
    """
    checks if a given question has child or not

    Return Either True or False
    """
    if QUESTION_CHILD_MAPPER.get(question):
        return True
    else:
        return False


def get_child_questions(question, QUESTION_CHILD_MAPPER, columns_in_dataset=None):
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
    child_question = QUESTION_CHILD_MAPPER.get(question, None)
    valid_questions = []
    for column in child_question:
        if column in columns_in_dataset:
            valid_questions.append(column)
    return valid_questions


def get_best_question_node_from_question_queue(question_queue, attribute="best_score", selection="min"):
    """
    Selects the best question node based on the given selection criteria and attribute.

    Parameters:
        question_queue (List[Node]): List of question nodes.
        attribute (str): The attribute to use for comparison (e.g., "score", "best_score", "cumulative_score").
        selection (str): Criteria for selection - "min" for the lowest value, "max" for the highest.

    Returns:
        Node: The node with the best value based on the selection criteria.
    """
    if not question_queue:
        return None  # No nodes to process

    try:
        if selection == "min":
            return min(question_queue, key=lambda node: getattr(node, attribute, float("inf")), default=None)
        elif selection == "max":
            return max(question_queue, key=lambda node: getattr(node, attribute, float("-inf")), default=None)
        else:
            raise ValueError(f"Invalid selection type: {selection}. Choose 'min' or 'max'.")
    except AttributeError:
        raise ValueError(f"Invalid attribute: {attribute}. Ensure nodes have this attribute.")
