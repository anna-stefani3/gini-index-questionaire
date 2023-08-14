# These functions are used to navigate and get parts of an XML domain tree.

# replace all hyphens with underscores in node codes
#
function codehyphenstounderscores!( node)
    if haskey(node, "code")
        node["code"] = replace(node["code"], "-" => "_")
    end
    for i = 1:length( elements(node))
        codehyphenstounderscores!( elements(node)[i])
    end
    node
end


    
# gets all the concept nodes in the tree, including the root concept
# in position 1, and returns them as a vector
#
function getconcepts( node)
    concepts = Vector{String}()
    getconcepts!( node, concepts)
    concepts
end

function getconcepts!( node, concepts)
    children = elements(node)
    if length(children) > 0
        push!( concepts, node["code"])
        for i in 1:length(children)
            getconcepts!( children[i], concepts)
        end
    end
end
    
# generates a dictionary of concepts and their descendants in a
# set. This is used for removing concepts that have descendants in the
# assessment. Note that it doesn't generate all the descendants of the
# whole node itself.
#
function getdescendantsallconcepts( node)
    conceptsanddescendants = Dict{String}{Set{String}}()
    # get a vector of all concepts in the node, including the root
    # concept
    nodesubconcepts = getconcepts(node)
    # we don't want the root node itself in the descendants so we
    # start at position two of the node concepts
    for pos in 2:length(nodesubconcepts)
        nodecode = nodesubconcepts[pos]
        conceptnode = getnode(node, nodecode)
        # get the descendants by changing the descendants argument and
        # also returning it
        conceptsanddescendants[nodecode] = getdescendants(conceptnode) 
    end
    conceptsanddescendants
end
    
# get all the descendants of a node, returned as a set
#
function getdescendants( node)
    descendants = Set{String}()
    children = elements(node)
    if length(children) > 0
        for i in 1:length(children)
            child = children[i]
            code = child["code"]
            push!(descendants, code)
            getdescendants!(child, descendants)
        end
    end
    descendants
end

# changes the descendants argument, which is collecting all the nodes
# and their descendants in a dictioary
#
function getdescendants!( node, descendants)
    children = elements(node)
    if length(children) > 0
        for i in 1:length(children)
            child = children[i]
            code = child["code"]
            push!(descendants, code)
            getdescendants!(child, descendants)
        end
    end
end

# goes through the catdescendants and sees whether the ancestor has
# the nodename as a descendant. Returns true of false.
#
function isdescendant( ancestor, nodename, catdescendants)
    if haskey(catdescendants, ancestor)
        if nodename in catdescendants[ancestor]
            return true
        else
            return false
        end
    else
        return false
    end
end

     

# siblings are from the CAT and are Vector{Node} (alias for Array{EzXML.Node, 1})
#
function getsibcodes( siblings)
    sibnames = Vector{String}()
    for i = 1:length(siblings)
        push!( sibnames, uppercase(siblings[i]["code"]))
    end
    sibnames
end

function getnode( tree, nodecode)
    if tree["code"] == nodecode
        tree
    else
        foundnode = nothing
        foundnode = findnode( tree, nodecode, foundnode)
    end
end

# finds the node in the children. If there aren't any, then the value
# returned is nothing
#
function findnode( tree, nodecode, foundnode)
    children = elements(tree)
    if length(children) > 0
        for i in 1:length(children)
            if children[i]["code"] == nodecode
                foundnode = children[i]
            else
                foundnode = findnode( children[i], nodecode, foundnode)
            end
        end
    end
    foundnode
end

# returns a vector of all the node codes in the given xml tree
# including the root node code if there is one. 
#
function getallnodecodes( node)
    if haskey(node, "code")
        riskcodes = [node["code"]]
    else
        riskcodes = Vector{String}()
    end
    children = elements(node)
    for i = 1:length(children)
        getnodecodes!(children[i], riskcodes)
    end
    riskcodes
end

# changes the riskcodes argument
#
function getnodecodes!(node, riskcodes)
    push!(riskcodes, node["code"])
    children = elements(node)
    if length(children) > 0
        for i = 1:length(children)
            getnodecodes!(children[i], riskcodes)
        end
    end
end

# Need to get the nodes that have questions in them for a given node
# (usually the whole risk node). The qt has all risk questions and
# must have been loaded into Julia as an XML object using:
#
# readxml("/home/cdbfif/research/grist/xml/QT-working-age.xml").root
#
# returns an array of node codes that are in the risk cat AND have
# questions attached. If nolayer is true, the layer questions (i.e. ones that are about
# the assessor's "concern" rather than answers about the patient's
# state) are NOT included.
#
function getquestioncodes( node, qt, nolayers)
    nodecodes = getallnodecodes( node)
    # note that the qt doesn't have a root node code so all its nodecodes
    # are the questions (elements), including the dv. this is because it
    # is a flat structure with elements and no root node attributes.
    qtnodes = elements(qt) # nodes with questions for every risk
    questioncodes = Vector{String}()
    # go through the node codes to see if they have a question attached.
    for i = 1:length(qtnodes)
        qtcode = qtnodes[i]["code"]
        qtvalues = qtnodes[i]["values"]
        if nolayers # don't keep layer questions
            if qtcode in nodecodes && qtvalues !== "layer"
                push!(questioncodes,qtcode)
            end
        elseif qtcode in nodecodes
            push!(questioncodes,qtcode)
        end
    end
    questioncodes
end

# prints out the column name and its value for a dataframe
#
function showpatientdata( df)
    for i in names(df)
        println( i, " = ", df[1,i])
    end
end

