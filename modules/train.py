import sys
import pickle


sys.path.append('modules')

import models
import util

link = 'https://www.dropbox.com/s/11pujhqtcmvv00o/all_filtered.csv?dl=1'
data_st, data_item, internal_st_ids, internal_item_ids, items_select = util.get_ids(link)
graph_model = models.GraphWandering(data_st, data_item, len(internal_st_ids), len(internal_item_ids))
log_model = models.LMF(already_liked=graph_model.neighborhood_graph[0])
log_model.fit(data_st, data_item, len(internal_st_ids), len(internal_item_ids))
ensemble_model = models.Ensemble(log_model, graph_model)
course_selector = util.CourseSelector(items_select)
course_searcher = util.CourseSearcher(list(internal_item_ids.keys()))
id_to_course = {internal_item_ids[c]: c for c in internal_item_ids}

with open('ensemble.pickle', 'wb') as f:
    pickle.dump(ensemble_model, f)

with open('selector.pickle', 'wb') as f:
    pickle.dump(course_selector, f)

with open('searcher.pickle', 'wb') as f:
    pickle.dump(course_searcher, f)

with open('internal_item_ids.pickle', 'wb') as f:
    pickle.dump(internal_item_ids, f)

with open('internal_st_ids.pickle', 'wb') as f:
    pickle.dump(internal_st_ids, f)

with open('id_to_course.pickle', 'wb') as f:
    pickle.dump(id_to_course, f)
