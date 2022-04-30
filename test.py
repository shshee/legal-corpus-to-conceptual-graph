from turtle import pos
from regex import P
from underthesea import word_tokenize, chunk, pos_tag, ner, classify
from comparsionHandler import ComparisonHandler
from dataHandler import DataHandler
from query_handler import reduce_words
from query import query_data
from generate_data import data_type
from conceptualGraph import ConceptualGraph

test = ConceptualGraph(reduce_words(
    "Người đang hưởng trợ cấp thất nghiệp có được hưởng chế độ bảo hiểm y tế không?"))
# test2 = ConceptualGraph(reduce_words(
#     "hưởng hiểm y tế trợ cấp thất nghiệp"))

# test3 = ComparisonHandler(test, test2)
# #test.print()
# print(test3.getSimilarityScore())
dir = "./data/"
dataHandler = DataHandler(
    dir+"laws.json", dir+"articles.json", dir+"rules.json", dir+"lookups.json")

dataHandler.compare(test)
