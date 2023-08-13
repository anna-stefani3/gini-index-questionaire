import xml.etree.ElementTree as ET
import json

tree = ET.parse("load-knowledge.xml")


def xml_to_dict(xml_string: str):
    root = ET.fromstring(xml_string)
    result = {}
    for child in root:
        name = child.attrib["code"].replace("-", "_")
        if len(child) == 0:
            result[name] = name
        else:
            result[name] = xml_to_dict(ET.tostring(child))
    return result


def get_child_question_mapper(data: [dict, str], parent: str, parsed_data: dict = {}):
    if type(data) == dict:
        names = list(data.keys())
        parsed_data[parent + "_mg"] = [name + "_mg" for name in names]
        for name in names:
            parsed_data = get_child_question_mapper(data[name], name, parsed_data)
    else:
        parsed_data[parent + "_mg"] = None
    return parsed_data


def string_replacer(string):
    replacer_dict = {
        "&quot;": '"',
        "&gt;": ">",
        "-": "_",
    }
    for key in replacer_dict:
        string = string.replace(key, replacer_dict[key])
    return string


def get_question_mapper(filename):
    with open(filename, "r") as xml_file:
        xml_string = xml_file.read()
    root = ET.fromstring(xml_string)
    result = {}
    for child in root:
        code = child.attrib["code"]
        question = child.attrib["question"]
        values = child.attrib["values"]
        code = string_replacer(code)
        question = string_replacer(question)
        if len(child) == 0:
            result[code + "_mg"] = {"question": question, "values": values}
    with open(filename.split(".")[0] + ".json", "w") as outfile:
        json.dump(result, outfile)
    return result


if __name__ == "__main__":
    with open("load-knowledge.xml", "r") as xml_file:
        xml_string = xml_file.read()

    # mapping the column with actual question and the value type of that question
    get_question_mapper("question-data.xml")


    # get the child questions for each question and None in case there is no child question
    result = xml_to_dict("".join(xml_string))
    parsed = get_child_question_mapper(result, "root")
    with open("child_question_mapper.json", "w") as outfile:
        json.dump(parsed, outfile)
