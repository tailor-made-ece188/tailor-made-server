import re
import json
import pprint
data = {}
with open('lykdatResponse.json') as f:
    data = json.load(f)
    data = data["data"]["result_groups"]


def filterArr(group):
    data = group["similar_products"]
    imageRegEx = '^.*.(jpe?g|png|JPE?G)$'
    filteredData = [el for el in data if re.search(
        imageRegEx, el.get("matching_image", ""))]
    filteredData = filteredData[0:5]
    return filteredData


filteredData = list(map(lambda group: filterArr(group), data))
pprint.pprint(filteredData)
