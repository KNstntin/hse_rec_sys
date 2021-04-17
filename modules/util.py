import pandas as pd
from fuzzywuzzy import process


def get_ids(source):
    raw_data = pd.read_csv(source)
    internal_st_ids = dict()
    internal_item_ids = dict()
    data_st = list()
    data_item = list()
    items_select = list()
    for x in raw_data.iloc:
        name = x['Фамилия'] + ' ' + x['Имя'] + ' ' + x['Отчество']
        if name not in internal_st_ids:
            internal_st_ids[name] = len(internal_st_ids)
        data_st.append(internal_st_ids[name])
        curriculum = str(x['Учебный план факультета'])
        if len(curriculum) > 3:
            if curriculum[:2] == 'МЭ':
                curriculum = curriculum[8:]
            elif curriculum[:3] == 'Мат':
                curriculum = curriculum[9:]
            elif curriculum[0] == 'Э':
                curriculum = curriculum[7:]
            else:
                curriculum = curriculum[5:]
            split = curriculum.split()
            if len(split) > 2 and (split[2] == 'Майнор' or split[2] == 'Минор'):
                curriculum = ' '.join(split[0:2] + split[3:])
            if curriculum[7] == curriculum[-1] == '"':
                curriculum = curriculum[:7] + curriculum[8:-1]
            if (curriculum[7:] == 'Интеллектуальный\xa0анализ\xa0данных'):
                curriculum = curriculum[:7] + 'Интеллектуальный анализ данных'
            elif curriculum[7:] == 'Навыки XXI века: 4 "К" (Коммуникация, Креативность, Критическое мышление, Командная работа)':
                curriculum = curriculum[:7] +\
                             'Майнор "Навыки XXI века: 4 "К" (Коммуникация. Креативность, Критическое мышление, Командная работа)"'
            elif curriculum[7:] == '"История театра. Театр и государство"' or curriculum[
                                                                              7:] == '"История театра.Театр и государство"':
                curriculum = curriculum[:7] + 'История театра'
            elif curriculum[7:] == 'Испания и испанский мир':
                curriculum = curriculum[:7] + 'Испания'
            elif curriculum == 'Культура европейского средневековья':
                curriculum = curriculum[:7] + 'Культура европейского средневековья'
            elif curriculum == 'Мир глазами физиков: от черных дыр к кубитам':
                curriculum = curriculum[:7] + 'Мир глазами физиков: от черных дыр до кубитов'
        else:
            curriculum = None
        if curriculum is not None:
            course = str(x['Наименование дисциплины']) + '\n' + curriculum
        else:
            course = str(x['Наименование дисциплины'])
        if course not in internal_item_ids:
            internal_item_ids[course] = len(internal_item_ids)
        data_item.append(internal_item_ids[course])

        if len(internal_item_ids) - 1 == data_item[-1] and pd.notnull(x['Курс по учебному плану']):
            course_degree = str(x['Курс по учебному плану']).split()
            if course_degree[0] == 'Специалисты':
                course_degree[0] = 'Специалитет'
            items_select.append((data_item[-1], int(course_degree[-2]), course_degree[0]))
    return data_st, data_item, internal_st_ids, internal_item_ids, items_select


class CourseSearcher:
    def __init__(self, courses):
        self.courses = courses

    def search(self, demand, k):
        return [x[0] for x in process.extract(demand, self.courses, limit=k)]


class CourseSelector:
    def __init__(self, items):
        self.items = items
        self.default = [item[0] for item in items]

    def select(self, degree=None, course_min=-1, course_max=7):
        if degree is not None:
            assert degree in {'Бакалавриат', 'Специалитет', 'Магистратура'  }
            return [item[0] for item in self.items if (course_min <= item[1] <= course_max and item[2] == degree)]
        else:
            return self.default

