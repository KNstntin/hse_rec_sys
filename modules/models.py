import pandas as pd
import random

from implicit.lmf import LogisticMatrixFactorization
from scipy.sparse import csr_matrix


class GraphWandering:
    def __init__(self, data_st, data_item, jumps=1):
        assert type(jumps) is int and jumps > 0, 'Incorrect jumps'
        self.neighborhood_graph = [dict(),
                                   dict()]
        for i, j in zip(data_st, data_item):
            if i not in self.neighborhood_graph[0]:
                self.neighborhood_graph[0][i] = set()
            self.neighborhood_graph[0][i].add(j)
            if j not in self.neighborhood_graph[1]:
                self.neighborhood_graph[1][j] = set()
            self.neighborhood_graph[1][j].add(i)
        self.jumps = jumps

    def _wander(self, ind, recommendation_list, selected_items=None):
        for _ in range(self.jumps):
            ind = random.choice(list(self.neighborhood_graph[0][ind]))
            ind = random.choice(list(self.neighborhood_graph[1][ind]))
        if selected_items is not None:
            s = self.neighborhood_graph[0][ind] & set(selected_items)
            if len(s) == 0:
                return
            ind = random.choice(list(s))
        else:
            ind = random.choice(list(self.neighborhood_graph[0][ind]))
        recommendation_list[ind] = recommendation_list.get(ind, 0) + 1

    def recommend(self, user, k, selected_items=None, number_of_wanderings=1000):
        assert user in self.neighborhood_graph[0], 'User is not in neighborhood graph'
        assert number_of_wanderings > 0, 'Incorrect number_of_wanderings'
        if selected_items is not None:
            selected_items = set(selected_items)
        recommendation_list = dict()
        for j in range(number_of_wanderings):
            self._wander(user, recommendation_list, selected_items)
        return sorted([item for item in recommendation_list.items() if item[0] not in self.neighborhood_graph[0][user]],
                      key=lambda x: x[1], reverse=True)[0:k]

    def recommend_item_based(self, k, choice, selected_items=None, number_of_wanderings=1000):
        assert len(choice) != 0, 'Given an empty list of chosen items'
        assert number_of_wanderings > 0, 'Incorrect number_of_wanderings'
        recommendation_list = dict()
        for j in range(number_of_wanderings):
            self._wander(random.choice(list(choice)), recommendation_list, selected_items)
        return sorted([item for item in recommendation_list.items() if item[0] not in choice],
                      key=lambda x: x[1], reverse=True)[0:k]


class LMF:
    def __init__(self, factors=200, iterations=100, regularization=1, neg_prop=10, already_liked=None):
        self.model = LogisticMatrixFactorization(factors, iterations=iterations,
                                                 regularization=regularization, neg_prop=neg_prop)
        self._already_liked = already_liked
        self._fitted = False
        self._user_items = None
    
    def fit(self, data_st, data_item, len_st_set, len_item_set):
        data = csr_matrix(([1] * len(data_st), (data_item, data_st)),
                          shape=(len_item_set, len_st_set))
        self._user_items = data.T.tocsr()
        self.model.fit(data, show_progress=False)
        self._fitted = True

    def recommend(self, user, k, selected_items=None):
        assert self._fitted, 'Model is not fitted'
        if selected_items is not None and self._already_liked is not None:
            if len(selected_items) != 0:
                return self.model.rank_items(user, self._user_items,
                    [item for item in selected_items if item not in self._already_liked[user]])[:k]
            else:
                return []
        else:
            return self.model.recommend(user, self._user_items, k, filter_already_liked_items=True)

    def recommend_item_based(self, k, choice, selected_items=None):
        assert self._fitted, 'Model is not fitted'
        assert len(choice) != 0, 'Given an empty list of chosen items'
        similar_items = [self.model.similar_items(x, 5*k) for x in choice]
        if selected_items is not None:
            d_list = [{e[0]: e[1] for e in similar_items[i] if (e[0] not in choice and e[0] in selected_items)}
                      for i in range(len(similar_items))]
        else:
            d_list = [{e[0]: e[1] for e in similar_items[i] if e[0] not in choice}
                      for i in range(len(similar_items))]
        results = dict()
        for d in d_list:
            for key in d:
                results[key] = results.get(key, 0) + d[key]
        return sorted(results.items(), key=lambda x: x[1], reverse=True)[:k]


class Ensemble:
    def __init__(self, *models):
        self.models = models

    def _shuffle(self, lists):
        result = list()
        i = 0
        while True:
            changed = False
            for j in range(len(lists)):
                if i < len(lists[j]):
                    result.append(lists[j][i])
                    changed = True
            if not changed:
                break
            i += 1
        recommendation = list()
        for x in result:
            if x[0] not in recommendation:
                recommendation.append(x[0])
        return recommendation

    def recommend(self, user, k_list, selected_items=None):
        assert len(k_list) == len(self.models), 'Length of k_list does not fit number of models'
        results = list()
        for model, k in zip(self.models, k_list):
            results.append(model.recommend(user, k, selected_items))
        return self._shuffle(results)

    def recommend_item_based(self, k_list, choice, selected_items=None):
        assert len(k_list) == len(self.models), 'Length of k_list does not fit number of models'
        results = list()
        for model, k in zip(self.models, k_list):
            results.append(model.recommend_item_based(k, choice, selected_items))
        return self._shuffle(results)


