import os
import shutil

import numpy as np
from datetime import datetime
import uuid

from crowdsorting.app_resources.sorting_algorithms.ACJ import ACJ

# Note - this algorithm takes 0.5*n^2 - 5*(n/10) comparisons to complete,
# where n is the number of documents in data


class ACJProxy:
    def __init__(self, project_name):
        from crowdsorting.settings.configurables import PICKLES_PATH
        self.acj = None
        self.number_of_docs = 0
        self.rounds = 0
        self.no_more_pairs = False
        self.project_name = project_name
        self.logPath = f"{PICKLES_PATH}/{self.project_name}"
        self.remaining_in_round = []
        self.served_not_returned = dict()
        self.finished = False
        self.total_comparisons = 0
        self.total_pairs_served = 0

    @staticmethod
    def get_algorithm_name():
        return "Adaptive Comparative Judgment"

    def initialize_selector(self, data, rounds=15, maxRounds=10, noOfChoices=1,
                   logPath=None, optionNames=None):
        if optionNames is None:
            optionNames = ["Choice"]
        if not logPath is None:
            self.logPath = logPath
        if not os.path.isdir(self.logPath):
            os.mkdir(self.logPath)
        if not os.path.isdir(f'{self.logPath}/logs'):
            os.mkdir(f'{self.logPath}/logs')
        print("creating acj")
        self.number_of_docs = len(data)
        # self.total_comparisons = int(0.5*(self.number_of_docs**2) - 5*(self.number_of_docs / 10))
        self.rounds = rounds
        dat = np.asarray(data)
        np.random.shuffle(dat)
        # self.acj = ACJ(dat, maxRounds, noOfChoices, f'{self.logPath}/logs', optionNames)
        self.acj = ACJ(dat, maxRounds, noOfChoices, None, optionNames)
        self.acj.nextIDPair()
        self.roundList = self.acj.roundList[:]
        self.no_more_pairs = False
        self.total_comparisons = int(self.rounds*(self.number_of_docs/2))
        self.pair_cutoff = int(self.rounds*(self.number_of_docs/2))

    def get_round_list(self):
        return self.roundList

    # def get_pair(self, number_of_docs, allDocs):
    def get_pair(self):
        if self.no_more_pairs:
            return "project is over"
        try:
            if isinstance(self.acj, type(None)):
                # self.unpickle_acj(number_of_docs)
                return "no acj created yet"
        except FileNotFoundError:
            return False
        #int(rounds*(length/2))
        if self.total_pairs_served >= self.pair_cutoff:
            self.no_more_pairs = True
            return "project is over"

        if len(self.roundList) == 0 and len(self.served_not_returned) == 0:
            self.no_more_pairs = True
            return "project is over"

        if len(self.roundList) == 0:
            return "waiting for round to turn over"

        acj_pair = self.roundList.pop()
        if isinstance(acj_pair, type(None)):
            self.no_more_pairs = True
            return "no pair available"
        # doc_one_name = self.acj.getScript(acj_pair[0])
        # doc_two_name = self.acj.getScript(acj_pair[1])
        pair_id = uuid.uuid4().hex
        # if acj_pair is None:
        #     return "no pair available"
        # doc_one = False
        # doc_two = False
        # for doc in allDocs:
        #     if doc.name == doc_one_name:
        #         doc_one = doc
        #     if doc.name == doc_two_name:
        #         doc_two = doc
        #     if doc_one and doc_two:
        #         break
        # doc_pair = DocPair(doc_one, doc_two)
        # if not doc_one or not doc_two:
        #     return "no pair available"
        self.served_not_returned[pair_id] = acj_pair
        self.total_pairs_served += 1
        return (acj_pair[0], acj_pair[1], pair_id)

    def make_comparison(self, preferred_id, unpreferred_id):
        self.acj.comp([preferred_id, unpreferred_id], True)

    def new_round(self):
        print(f'trying to start new round')
        self.acj.step = len(self.acj.roundList)
        self.acj.nextPair()
        print(f'old ACJProxy roundList: {self.roundList}')
        self.roundList = self.acj.roundList[:]
        print(f'new ACJProxy roundList: {self.roundList}')

    def make_judgment(self, pair_id, easier_doc_name, harder_doc_name, duration,
                      judge_name='Unknown'):
        try:
            acj_pair = self.served_not_returned[pair_id]
        except KeyError:
            return "pair not found"

        easier_doc_id = self.acj.getID(easier_doc_name.name)
        harder_doc_id = self.acj.getID(harder_doc_name.name)

        if acj_pair[0] == easier_doc_name.name:
            outcome = False
        elif acj_pair[0] == harder_doc_name.name:
            outcome = True
        else:
            return "pair id maps to wrong doc ids"

        self.acj.comp(acj_pair, outcome, reviewer=judge_name, time=duration)
        del self.served_not_returned[pair_id]
        if len(self.roundList) == 0 and len(self.served_not_returned) == 0:
            self.acj.step = len(self.acj.roundList) + 1
            self.acj.nextIDPair()
            self.roundList = self.acj.roundList[:]
        return True

    def get_sorted(self):
        # if isinstance(self.acj, type(None)):
        #     self.unpickle_acj(len(allDocs))
        # if len(allDocs) < 1:
        #     return "No files in database"
        sortedFiles = [x[0] for x in self.acj.results()[0]]
        return sortedFiles

    def get_possible_judgments_count(self):
        return self.get_total_comparisons_left() + self.get_number_comparisons_made()
        """total = int(self.rounds * (self.number_of_docs / 2))
        if total < 1:
            total = 1
        print(f'returning number of pairs: {total}')
        return total"""

    def get_confidence(self):
        return self.acj.reliability()[0]

    def get_number_comparisons_made(self):
        return self.acj.getComparisonsMade()

    def get_total_comparisons_left(self):
        return self.total_comparisons - self.acj.getComparisonsMade()

    def delete_self(self):
        print(f"deleting {self.acj} pickles")
        if os.path.exists(f"crowdsorting/app_resources/sorter_instances/{self.project_name}.pkl"):
            os.remove(f"crowdsorting/app_resources/sorter_instances/{self.project_name}.pkl")
        if os.path.exists(self.logPath):
            shutil.rmtree(self.logPath)

    def get_round_list(self):
        return self.roundList
        # return self.acj.unservedRoundList

    def finished(self):
        return self.no_more_pairs