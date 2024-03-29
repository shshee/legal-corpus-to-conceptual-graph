from cgitb import lookup
import enum
from scipy.fftpack import idct
from comparsionHandler import ComparisonHandler
from conceptualGraph import ConceptualGraph
from enums import DataPathTypes
import json

from query_handler import reduce_words


class DataHandler:
    def __init__(self, lawsPath, articlesPath, rulesPath, lookupsPath):
        self.laws = self.__retrieveData(lawsPath)
        self.articles = self.__retrieveData(articlesPath)
        self.rules = self.__retrieveData(rulesPath)
        self.lookups = self.__retrieveData(lookupsPath)

        self.graphs = self.__conceptualizeKeyphrase()

    def __retrieveData(self, path):
        """
        Input: type of data that we need to retrive
        Output: list data in this file
        """
        result = []
        # Read list titles of laws
        f = open(path, encoding="utf8")

        # returns JSON object as
        # a dictionary
        data = json.load(f)

        # Iterating through the json
        # list
        for item in data:
            result.append(item)

        f.close()
        return result

    def __conceptualizeKeyphrase(self):
        """
        Output: list data about articles and rules converted to conceptual graphs
        """
        result = []
        for article in self.articles:
            keyphrase = article["keyphrase"]
            if keyphrase:
                result.append((ConceptualGraph(keyphrase),
                              article["id"], DataPathTypes.ARTICLES))

        for rule in self.rules:
            keyphrase = rule["keyphrase"]
            if keyphrase:
                result.append(
                    (ConceptualGraph(keyphrase), rule["id"], DataPathTypes.RULES))

        return result

    def getData(self, type):
        """
        Input: Enum type of data that we want to get
        Output: list json objects of input type
        """
        if type == DataPathTypes.LAWS:
            return self.laws
        elif type == DataPathTypes.ARTICLES:
            return self.articles
        elif type == DataPathTypes.RULES:
            return self.rules
        elif type == DataPathTypes.LOOKUPS:
            return self.lookups

    def compare(self, graph):
        result = []
        """
        Input: Graph of query that we want to compare
        Output: list of top similarities of this graph to data
        """
        for data in self.graphs:
            # print("------------------------")
            comparisonHandler = ComparisonHandler(graph, data[0])
            add_value = (
                # Id of this type of data
                data[1],
                # get title of this data,
                self.getArticleTitle(data[1], data[2]),
                # get index of this rule in article
                self.getRuleTitle(
                    data[1], True) if data[2] == DataPathTypes.RULES else "",
                # get law code of this data,
                ', '.join(self.getCodeList(data[1], data[2])),
                # Get comparison score
                str(self.applyYearReleaseCount(
                    comparisonHandler.getSimilarityScore(data[2]), data[1], data[2])),
                # str(comparisonHandler.getSimilarityScore(data[2])),
                # get graph of similarity
                str(round(comparisonHandler.conceptual_similarity(), 5)),
                # get graph of similarity
                str(round(comparisonHandler.relational_similarity(), 5)),
                str(round(comparisonHandler.nGcs, 5)),
                str(round(comparisonHandler.nG1s, 5)),
                str(round(comparisonHandler.nG2s, 5)),
                comparisonHandler
            )
            result.append(add_value)
            # print("Nodes:", data[0].getNodes(), "- Score of", data[1], "is",comparisonHandler.getSimilarityScore())
        return result

    def getDataFromId(self, id, type):
        return list(filter(lambda val: val["id"] == id, self.articles if type ==
                           DataPathTypes.ARTICLES else self.rules))[0]

    def getLookUpFromId(self, id, type):
        lookUpId = self.getDataFromId(id, type)["lookUpId"]
        return list(filter(lambda lk: lk["id"] == lookUpId, self.lookups))[0]

    def getCodeList(self, id, type):
        return self.getLookUpFromId(id, type)['laws']

    def getArticleTitle(self, id, dataType):
        """
        Input: id and type of rule or article
        Output: string title of this article 
        """
        if dataType == DataPathTypes.ARTICLES:
            return self.getDataFromId(id, DataPathTypes.ARTICLES)["title"]
        elif dataType == DataPathTypes.RULES:
            return self.getRuleTitle(id, False)

    def getRuleTitle(self, id, onlyIndex):
        """
        Input: id and type of rule and if we only want to get index of this rule in article turn onlyIndex to True
        Output: string title of the parent article of this rule 
        """
        lookUp = self.getLookUpFromId(id, DataPathTypes.RULES)

        if(onlyIndex):
            content = self.getDataFromId(id, DataPathTypes.RULES)["content"]
            return "Khoản " + content.split(".")[0]
        else:
            return self.getArticleTitle(lookUp["article"], DataPathTypes.ARTICLES)

    def getContentData(self, id, type):
        lookUp = self.getLookUpFromId(id, type)
        refers = []
        for refer in lookUp["references"]:
            refers.append(refer)

        content = ""
        if type == DataPathTypes.ARTICLES:
            for ruleId in lookUp["rules"]:
                data = self.getDataFromId(
                    ruleId, DataPathTypes.RULES)
                content = content + \
                    str(data["content"]) + "\n"
                for refer in data["references"]:
                    refers.append(refer)
        elif type == DataPathTypes.RULES:
            data = self.getDataFromId(
                id, DataPathTypes.RULES)
            content = str(data["content"]) + "\n"
            for refer in data["references"]:
                refers.append(refer)

        return (content, refers)

    def getLawFromCode(self, code):
        return list(filter(lambda law: law["code"] == code, self.laws))[0]

    def getArticleFromRule(self, id):
        lookUp = self.getLookUpFromId(id, DataPathTypes.RULES)
        return self.getDataFromId(lookUp["article"], DataPathTypes.ARTICLES)

    def getLawTitlesFromList(self, id, type):
        result = []
        for code in self.getCodeList(id, type):
            result.append(self.getLawFromCode(code)['title'])
        return result

    def getDataGraphFromId(self, id):
        return list(filter(lambda graph: graph[1] == id, self.graphs))

    def getContentFromId(self, itemId):
        data = self.getDataGraphFromId(itemId)
        type = data[0][2] if data else DataPathTypes.RULES
        result = "Theo "
        titles = self.getLawTitlesFromList(itemId, type)
        for index, code in enumerate(self.getCodeList(itemId, type)):
            ending = ":\n" if index + \
                1 == len(self.getCodeList(itemId, type)) else " và "
            result = result + titles[index] + " số "+code + ending

        if type == DataPathTypes.RULES:
            result = result + self.getRuleTitle(itemId, True) + " thuộc "

        article = self.getArticleTitle(itemId, type)
        contentData = self.getContentData(itemId, type)
        result = result + article + "\n" + contentData[0]
        if contentData[1]:
            result = result + "\n\n"
            for refer in contentData[1]:
                if refer[0] == 'l':
                    lookup = list(
                        filter(lambda lk: lk["id"] == refer, self.lookups))[0]
                    result = result + self.getContentFromId(lookup["article"])
                else:
                    result = result + self.getContentFromId(refer)
        return result

    def applyYearReleaseCount(self, score, id, type):
        return round(score + (self.getLookUpFromId(id, type)['lastest'] / 10000),5)

    def print(self):
        print(self.laws)
