import json
from pprint import pprint

with open('cornell.json') as data_file:    
    data = json.load(data_file)

pprint(data)
print(len(data['cornell']))
