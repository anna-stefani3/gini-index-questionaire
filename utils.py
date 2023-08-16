import xml.etree.ElementTree as ET
import json


"""
load-knowledge.xml file contains the hierarchical struture of the questionaire.
Using this File we can extract the child question for each parent question
"""
# reads the XML file "load-knowledge.xml"
tree = ET.parse("load-knowledge.xml")

# converts the XML data into Dictionary
def xml_to_dict(xml_string: str):
    """
    Summary
    Args:
        xml_string (str): XML data in string Format 

    Process:
        Step 1) Reads XML String data as XML Element Tree
        Step 2) Loop each child node from root node
        Step 3) if there is no child node for the child then add child name into the result dictionary
        Step 4) Else parse the child ET using Recursion
        Step 5) Gets the Dictionary as Tree Structure or Hierarchical Structure
    Returns:
        Dictionary (Tree Like struture)
        Looks like this
        {
            "column_1" : {
                "column_2" : {
                    "column_3" : "column_3",
                    "column_4" : "column_4",
                    "column_5" : "column_5",
                },
                "column_6" : {
                    "column_7" : "column_7",
                    "column_8" : "column_8",
                },
                "column_9" : {
                    "column_10" : "column_10",
                    "column_11" : "column_11",
                    "column_12" : "column_12",
                    "column_13" : "column_14",
                    "column_14" : "column_15",
                },
            }
            "column_21" : {
                "column_22" : {
                    "column_23" : "column_23",
                    "column_24" : "column_24",
                    "column_25" : "column_25",
                }
            }
        }
    """
    # Reads XML String data as XML Element Tree
    root = ET.fromstring(xml_string)
    result = {}
    # parse each child node from root node
    for child in root:
        # get name sttribute of the child node and replace "-" with "_"
        name = child.attrib["code"].replace("-", "_")
        if len(child) == 0:
            # if there is no child node for this child then add it into result dictionary
            result[name] = name
        else:
            # else Recursively parse the XML data into the dict
            result[name] = xml_to_dict(ET.tostring(child))
    # final tree like dict structure
    return result


def get_child_question_mapper(data: [dict, str], parent: str, parsed_data: dict = {}):
    """_summary_

    Args:
        data (dict, str]): data type can be dict or string
        parent (str): name of parent node
        parsed_data (dict): passed with current state of the parsed_data. 
            Defaults to {}.

    Returns:
        Dict : 
        contains list of child question for a given question
        Data looks like this
        {
            "column_1" : ["column_10", "column_15", "column_21"],
            "column_2" : ["column_11", "column_18", "column_29", "column_51"],
            "column_3" : None
        }

        where None means there is no Child Question for "column_3"
    """

    # if type of data == dict
    # then we need to parse through each child questions
    if type(data) == dict:
        # gets the list of names of the child questions
        names = list(data.keys())

        # adding question key with list of child questions as value
        # adding "_mg" to parent and child questions names
        parsed_data[parent + "_mg"] = [name + "_mg" for name in names]

        # adding key value pair for each child
        for name in names:
            # recursively adding data for child questions
            parsed_data = get_child_question_mapper(data[name], name, parsed_data)
    else:
        # incase parent type == str then there is no child question
        # so adding None to it
        parsed_data[parent + "_mg"] = None

    # returning complete dictionary of parent and child questions data
    return parsed_data


def string_replacer(string):
    """util funtion to replace substring
    &quot; to "
    &gt; to  >
    - to _
    for example -> hto-result into hto_result
    """
    replacer_dict = {
        "&quot;": '"',
        "&gt;": ">",
        "-": "_",
    }
    for key in replacer_dict:
        string = string.replace(key, replacer_dict[key])
    return string


def get_question_mapper(filename):
    # reads the XML file
    with open(filename, "r") as xml_file:
        xml_string = xml_file.read()

    # converting XML string into ET (Element Tree)
    root = ET.fromstring(xml_string)

    # initialising with empty result dictionary
    result = {}
    for child in root:
        # getting code atrtibute from node
        code = child.attrib["code"]
        # getting question atrtibute from node
        question = child.attrib["question"]
        # getting values atrtibute from node
        values = child.attrib["values"]

        # replacing string values for code
        code = string_replacer(code)
        # replacing string values for question
        question = string_replacer(question)
        
        """
        NOTE: As the structure of "question-data.xml" is flat and not tree like
            we are ignoring any recursive parsing
        """
        if len(child) == 0:
            # adding question and values for the Code
            # adding "_mg" to code name (column name)
            result[code + "_mg"] = {"question": question, "values": values}

    with open(filename.split(".")[0] + ".json", "w") as outfile:
        # exporting the Dictionary result into JSON file
        json.dump(result, outfile)
    return result


if __name__ == "__main__":

    # opens and read "load-knowledge.xml" file as string data
    with open("load-knowledge.xml", "r") as xml_file:
        # xml_string contains string format of the XML file
        xml_string = xml_file.read()

    # mapping the column with actual question and the value type of that question
    get_question_mapper("question-data.xml")

    # getting tree structure in Dictionary Format
    result = xml_to_dict("".join(xml_string))

    # get the child questions for each question and None in case there is no child question
    parsed = get_child_question_mapper(result, "root")
    with open("child_question_mapper.json", "w") as outfile:
        # exporting the Dictionary data into "child_question_mapper.json" JSON file
        json.dump(parsed, outfile)
