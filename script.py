
########### SETUP AND CONFIGURATION ##########

import json
import sys
from pymongo import MongoClient
from bson import ObjectId
import datetime

# Encode BSON specific values into JSON values
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId) or isinstance(o, datetime.date):
            return str(o)
        return json.JSONEncoder.default(self, o)

# Instantiate singleton to use throughout program
jsonEncoder = JSONEncoder()

# Attempt to retrieve arguments passed in with program call
try:
    indicator_id = sys.argv[1]
    # days_back = sys.argv[2]
    # sources = sys.argv[3]
except IndexError:
    print "Medusa was not called with the proper arguments. Please check your input and try again"
    sys.exit(0)

# Connect to Local MongoDB Instance
client = MongoClient()
db = client.test

nodes = []
edges = []
references = []

########### QUERY 1 ##########

indicators = []
for ind in db.indicators.find(
        filter={"_id": indicator_id}, 
        projection={
            "value": 1,
            "status": 1,
            "source.name": 1,
            "source.instances.date": 1,
            "source.instances.reference": 1}):
    indicators.append(ind)

# Check if indicator_id exists
# If yes, add indicator node
if (len(indicators) > 0):
    nodes.append({
        "id": indicator_id,
        "type": "indicator",
        "value": indicator_id 
    })
else:
    print "Invalid Indicator Id. No indicator found"
    sys.exit(0)
    
# Extract References and create nodes
for ind in indicators:
    for src in ind["source"]:
        for inst in src["instances"]:
            references.append(inst["reference"])
            node = {
                "id": str(inst["reference"]),
                "type": "reference",
                "value": inst["reference"]
            }
            nodes.append(node)

# Create Edges
for ind in indicators:
    for src in ind["source"]:
        for inst in src["instances"]:
            for ref in references:
                if "reference" in inst and inst["reference"] in references and {"from": str(ind["_id"]), "to": ref} not in edges:
                    edges.append({"from": str(ind["_id"]), "to": ref})

########### QUERY 2 ##########

analyzed_indicators = []
for ind in db.indicators.find(
        filter={
            "status": "Analyzed",
            "source.instances": {
                "$elemMatch": {
                    "reference": {"$in": references}
                }
            }
        }, 
        projection={
            "value": 1,
            "status": 1,
            "source.name": 1,
            "source.instances.date": 1,
            "source.instances.reference": 1}):
    analyzed_indicators.append(ind)

# Create nodes
for ind in analyzed_indicators:
    for src in ind["source"]:
        for inst in src["instances"]:
            node = {
                "id": str(ind["_id"]),
                "type": "indicator",
                "value": ind["value"]
            }
            if (node not in nodes):
                nodes.append(node)

# Create edges
for ind in analyzed_indicators:
    for src in ind["source"]:
        for inst in src["instances"]:
            for ref in references:
                edge = {
                    "from": str(ind["_id"]),
                    "to": ref
                }
                if inst["reference"] == ref and edge not in edges:
                    edges.append(edge)

########### DATA TRANSMISSION ##########

# Serialize nodes and edges by encoding to JSON
nodes = jsonEncoder.encode(nodes)
edges = jsonEncoder.encode(edges)

# print is a thin wrapper that formats inputs and
# calls the write function on a given object (default: sys.stdout)
print nodes + "SPLIT" + edges
