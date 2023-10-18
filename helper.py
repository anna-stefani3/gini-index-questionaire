import pandas as pd
import json


# reading the question mapping data from json file
def load_json_file(filename):
    with open(filename) as file:
        data = json.load(file)
    return data


def get_cleaned_data(base_path, dataset_name):
    file_path = "Child/child-adolescent-suic.csv"
    # reading the csv file where we defined "\\N" as Missing Data
    data = pd.read_csv(base_path + file_path, na_values="\\N")

    data.rename(columns={"friends_peers_mg": "friends_colleagues_mg"}, inplace=True)
    # Getting Required Columns from dataset
    data = data.iloc[:, 4:]

    # droping all rows which has missing class (Risk Score)
    data = data.dropna(subset=[dataset_name])

    # dropping rows where all the values are Missing Value
    data.dropna(how="all")

    # # replacing Missing Values with -999 constant number which will represent
    # "NO" as an answer for that question
    data = data.fillna(-999)  # there are various other methods we can implement for imputing the missing data
    return data


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
def convert_scale_columns_to_classes(data, QUESTION_MAPPER):
    for column in data.columns:
        if QUESTION_MAPPER.get(column) and QUESTION_MAPPER[column]["values"] == "scale":
            data[column] = data[column].apply(convert_to_low_medium_and_high_risk)
    return data


# gets the choices for each column name for the user to answer
def get_question_choices_data(dataset):
    question_choices_data = {}
    for column in dataset.columns:
        unique_answers = list(dataset[column].unique())
        if -999 in unique_answers:
            unique_answers.remove(-999)
        question_choices_data[column] = unique_answers

    return question_choices_data


# Calculated Gini Impurity for given List of Risk Labels
def gini_measure_of_impurity(labels, unique_labels={"high", "low", "medium"}):
    total_count = len(labels)
    if total_count == 0:
        return 0
    impurity = 1
    # unique_labels = set(labels)
    # print(f"UNIQUE LABELS => {unique_labels}")

    # Here Labels Represent "high", "medium" and "low" Risk Label
    # Thus Calculating the Gini Impurity based on Label
    for label in unique_labels:
        label_count = labels.count(label)
        label_prob = label_count / total_count
        impurity -= label_prob**2
    return impurity


# Aggregating the Gini Scores for a Given Question
def get_utility_score(dataset, question, unique_answers, DATASET_NAME):
    # initializing total_utility_score = 0
    total_utility_score = 0

    # Adding all Gini Scores for each uniques Answers for the given Question
    for answer in unique_answers:
        if answer == -999:
            continue
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


def has_child(question, QUESTION_CHILD_MAPPER):
    # returns if the specific question has child questions or not
    # returns only TRUE or FALSE
    if QUESTION_CHILD_MAPPER[question]:
        return True
    else:
        return False


def get_sorted_utility_scores_df(complete_dataset, choices_dataset, QUESTION_QUEUE):
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


def remove_question(remove_list, QUESTION_QUEUE):
    # looping through each column name in remove_list
    for question in remove_list:
        # removing specific question from QUESTION_QUEUE
        QUESTION_QUEUE.remove(question)


def add_child_questions(question, question_queue, QUESTION_MAPPER, QUESTION_CHILD_MAPPER):
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
        inserted = 0
        # looping throught each column in the child list
        for question in child_question:
            # if child column exist in QUESTION_MAPPER
            if QUESTION_MAPPER.get(question):
                inserted += 1
                # adding each child column into question_queue
                question_queue.insert(0, question)
    # print("      INSERTING ->" , inserted)
    return question_queue
