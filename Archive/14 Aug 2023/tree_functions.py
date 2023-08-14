def codehyphenstounderscores(node):
    if "code" in node:
        node["code"] = node["code"].replace("-", "_")
    for child in node.get("elements", []):
        codehyphenstounderscores(child)
    return node


# what are concepts in here??? As I am unable to see any word named "concept" or "concepts" in the XML data
def getconcepts(node):
    concepts = []
    getconcepts_recursive(node, concepts)
    return concepts


def getconcepts_recursive(node, concepts):
    children = node.get("elements", [])
    if len(children) > 0:
        concepts.append(node["code"])
        for child in children:
            getconcepts_recursive(child, concepts)


def getdescendantsallconcepts(node):
    conceptsanddescendants = {}
    nodesubconcepts = getconcepts(node)
    for pos in range(1, len(nodesubconcepts)):
        nodecode = nodesubconcepts[pos]
        conceptnode = getnode(node, nodecode)
        conceptsanddescendants[nodecode] = getdescendants(conceptnode)
    return conceptsanddescendants


def getdescendants(node):
    descendants = set()
    children = node.get("elements", [])
    if len(children) > 0:
        for child in children:
            code = child["code"]
            descendants.add(code)
            getdescendants_recursive(child, descendants)
    return descendants


def getdescendants_recursive(node, descendants):
    children = node.get("elements", [])
    if len(children) > 0:
        for child in children:
            code = child["code"]
            descendants.add(code)
            getdescendants_recursive(child, descendants)


def isdescendant(ancestor, nodename, catdescendants):
    if ancestor in catdescendants:
        return nodename in catdescendants[ancestor]
    return False


def getsibcodes(siblings):
    sibnames = []
    for sibling in siblings:
        sibnames.append(sibling["code"].upper())
    return sibnames


def getnode(tree, nodecode):
    if tree.get("code") == nodecode:
        return tree
    else:
        foundnode = findnode(tree, nodecode)
        return foundnode


def findnode(tree, nodecode):
    children = tree.get("elements", [])
    if len(children) > 0:
        for child in children:
            if child.get("code") == nodecode:
                return child
            else:
                foundnode = findnode(child, nodecode)
                if foundnode:
                    return foundnode


def getallnodecodes(node):
    riskcodes = []
    if "code" in node:
        riskcodes = [node["code"]]
    children = node.get("elements", [])
    for child in children:
        getnodecodes_recursive(child, riskcodes)
    return riskcodes


def getnodecodes_recursive(node, riskcodes):
    riskcodes.append(node["code"])
    children = node.get("elements", [])
    for child in children:
        getnodecodes_recursive(child, riskcodes)


def getquestioncodes(node, qt, nolayers):
    nodecodes = getallnodecodes(node)
    qtnodes = qt.get("elements", [])
    questioncodes = []
    for qtnode in qtnodes:
        qtcode = qtnode["code"]
        qtvalues = qtnode["values"]
        if nolayers:
            if qtcode in nodecodes and qtvalues != "layer":
                questioncodes.append(qtcode)
        elif qtcode in nodecodes:
            questioncodes.append(qtcode)
    return questioncodes


def showpatientdata(df):
    for col in df.columns:
        print(col, "=", df.iloc[0][col])
