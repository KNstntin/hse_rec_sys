import telebot

from modules import models
from modules import util


link = 'source to dataset'
data_st, data_item, internal_st_ids, internal_item_ids, items_select = util.get_ids(link)
graph_model = models.GraphWandering(data_st, data_item)
log_model = models.LMF(already_liked=graph_model.neighborhood_graph[0])
log_model.fit(data_st, data_item, len(internal_st_ids), len(internal_item_ids))
ensemble_model = models.Ensemble(log_model, graph_model)
course_selector = util.CourseSelector(items_select)
course_searcher = util.CourseSearcher(list(internal_item_ids.keys()))
id_to_course = {internal_item_ids[c]: c for c in internal_item_ids}

TOKEN = "token of bot"
bot = telebot.TeleBot(TOKEN)
user_dict = dict()

keyboard_recommend = telebot.types.ReplyKeyboardMarkup(True)
for row in [['Получить рекомендацию'], ['Добавить понравившийся курс', 'Указать систему подготовки и курс'],
            ['Вывести список указанных курсов', 'Удалить курс из указанного списка']]:
    keyboard_recommend.row(*row)

keyboard_degree = telebot.types.ReplyKeyboardMarkup(True)
for row in ['Бакалавриат', 'Специалитет', 'Магистратура']:
    keyboard_degree.row(row)

keyboard_no_choice = telebot.types.ReplyKeyboardMarkup(True)
keyboard_no_choice.row('Ни один из представленных', 'Вернуться назад')

keyboard_delete_all = telebot.types.ReplyKeyboardMarkup(True)
keyboard_delete_all.row('Удалить все', 'Вернуться назад')

hideboard = telebot.types.ReplyKeyboardRemove()


@bot.message_handler(commands=['start'])
def send_initial(message):
    text = 'Рекомендательная система курсов ВШЭ'
    bot.send_message(message.from_user.id, text, reply_markup=keyboard_recommend)


@bot.message_handler(commands=['help'])
def send_initial(message):
    text = 'Для рекоммендации нам необходимо узнать, что вам понравилось в обучении'
    bot.send_message(message.from_user.id, text, reply_markup=keyboard_recommend)


def show_liked(message):
    if (message.from_user.id not in user_dict or
            'choice' not in user_dict[message.from_user.id] or len(user_dict[message.from_user.id]['choice']) == 0):
        bot.send_message(message.from_user.id,
                         'Вы не указали ни одного курса',
                         reply_markup=keyboard_recommend)
        return False
    else:
        text = str()
        for i, course in enumerate(user_dict[message.from_user.id]['choice']):
            text += f'\n\n{i + 1}) {id_to_course[course]}'
        bot.send_message(message.from_user.id,
                         'Ваши указанные курсы:' + text,
                         reply_markup=keyboard_recommend)
        return True


@bot.message_handler(content_types=['text'])
def send_messages(message):
    if message.text.lower() == 'добавить понравившийся курс':
        bot.send_message(message.from_user.id,
                         'Введите название курса по выбору, курса майнора или факультатива',
                         reply_markup=hideboard)
        bot.register_next_step_handler(message, get_choice)

    elif message.text.lower() == 'получить рекомендацию':
        try:
            recommendation = get_recommendation(message)
            if len(recommendation) == 0:
                bot.send_message(message.from_user.id,
                                 'Предоставленной вами информации недостаточно, чтобы дать рекоммендацию')
            else:
                result = str()
                for i, x in enumerate(recommendation):
                    if x in id_to_course:
                        result += f'\n\n{str(i + 1)}) {id_to_course[x]}'
                bot.send_message(message.from_user.id,
                                 'Возможно, вас заинтересуют следующие курсы (в порядке приоритета):\n' + result,
                                 reply_markup=keyboard_recommend)
        except AssertionError:
            bot.send_message(message.from_user.id, 'Вы не указали ни одного курса')

    elif message.text.lower() == 'вывести список указанных курсов':
        show_liked(message)

    elif message.text.lower() == 'удалить курс из указанного списка':
        if show_liked(message):
            bot.send_message(message.from_user.id,
                             'Введите через пробел номера курсов, которые бы вы хотели удалить',
                             reply_markup=keyboard_delete_all)
            bot.register_next_step_handler(message, delete_courses)
        else:
            bot.send_message(message.from_user.id,
                             'Вы не указали ни одного курса')

    elif message.text.lower() == 'указать систему подготовки и курс':
        bot.send_message(message.from_user.id,
                         'На какой системе подготовки вы учитесь? (Бакалавриат, Специалитет, Магистратура)',
                         reply_markup=keyboard_degree)
        bot.register_next_step_handler(message, set_degree)

    else:
        bot.send_message(message.from_user.id, 'Выберите желаемую опцию')


def delete_courses(message):
    if message.text.lower() == 'вернуться назад':
        bot.send_message(message.from_user.id, 'Выберите желаемую опцию', reply_markup=keyboard_recommend)
    elif message.text.lower() == 'удалить все':
        user_dict[message.from_user.id].pop('choice')
        bot.send_message(message.from_user.id, 'Все курсы удалены', reply_markup=keyboard_recommend)
    else:
        try:
            for i in sorted(list(map(int, message.text.split())), reverse=True):
                if 0 <= i - 1 < len(user_dict[message.from_user.id]['choice']):
                    user_dict[message.from_user.id]['choice'].pop(i - 1)
            bot.send_message(message.from_user.id, 'Все вами указанные курсы удалены', reply_markup=keyboard_recommend)
        except BaseException:
            bot.send_message(message.from_user.id, 'Некорректное сообщение, повторите попытку')
            bot.register_next_step_handler(message, delete_courses)


def get_choice(message):
    if message.from_user.id not in user_dict:
        user_dict[message.from_user.id] = dict()
    user_dict[message.from_user.id]['temporary'] = course_searcher.search(message.text, 4)
    text = str()
    for i, x in enumerate(user_dict[message.from_user.id]['temporary']):
        text += f'\n\n{i + 1}): {x}'
    bot.send_message(message.from_user.id,
                     'Который из ниже представленных вы имели ввиду? Введите номер' + text,
                     reply_markup=keyboard_no_choice)
    bot.register_next_step_handler(message, append_choice)


def append_choice(message):
    try:
        if message.text.lower() == 'ни один из представленных':
            user_dict[message.from_user.id].pop('temporary')
            bot.send_message(message.from_user.id,
                             'Похоже, указанный курс не содержится в нашей базе данных', reply_markup=keyboard_recommend)
        elif message.text.lower() == 'вернуться назад':
            user_dict[message.from_user.id].pop('temporary')
            bot.send_message(message.from_user.id, 'Выберите желаемую опцию', reply_markup=keyboard_recommend)
        else:
            number = int(message.text) - 1
            assert number >= 0, 'Number less than 0'
            if 'choice' not in user_dict[message.from_user.id]:
                user_dict[message.from_user.id]['choice'] = list()
            course_id = internal_item_ids[user_dict[message.from_user.id]['temporary'][number]]
            if course_id not in user_dict[message.from_user.id]['choice']:
                user_dict[message.from_user.id]['choice'].append(course_id)
                bot.send_message(message.from_user.id, 'Ваше предпочтение будет учтено при рекоммендации',
                                 reply_markup=keyboard_recommend)
            else:
                bot.send_message(message.from_user.id, 'Этот курс уже был указан',
                                 reply_markup=keyboard_recommend)
            user_dict[message.from_user.id].pop('temporary')

    except AssertionError:
        bot.send_message(message.from_user.id, 'Вы ввели слишком малое число. Повторите попытку')
        bot.register_next_step_handler(message, append_choice)

    except IndexError:
        bot.send_message(message.from_user.id, 'Вы ввели слишком большое число. Повторите попытку')
        bot.register_next_step_handler(message, append_choice)

    except BaseException:
        bot.send_message(message.from_user.id, 'Вы ввели не число. Повторите попытку')
        bot.register_next_step_handler(message, append_choice)


def set_degree(message):
    try:
        degree = message.text
        assert degree in {'Бакалавриат', 'Магистратура', 'Специалитет'}
        if message.from_user.id not in user_dict:
            user_dict[message.from_user.id] = dict()
        user_dict[message.from_user.id]['degree'] = degree
        bot.send_message(message.from_user.id, 'Введите курс вашего обучения', reply_markup=hideboard)
        bot.register_next_step_handler(message, set_course)
    except AssertionError:
        bot.send_message(message.from_user.id, 'Сообщение некорректно', reply_markup=keyboard_recommend)


def set_course(message):
    try:
        course = int(message.text)
        degree = user_dict[message.from_user.id]['degree']
        assert (course >= 1 and degree in {'Бакалавриат', 'Магистратура', 'Специалитет'} and
                (degree == 'Специалитет' and course <= 6 or
                 degree == 'Бакалавриат' and course <= 4 or
                 degree == 'Магистратура' and course <= 2))
        user_dict[message.from_user.id]['course'] = course
        bot.send_message(message.from_user.id,
                         f'Ваша форма обучения - {user_dict[message.from_user.id]["degree"]}, курс обучения - {course}',
                         reply_markup=keyboard_recommend)
    except BaseException:
        bot.send_message(message.from_user.id, 'Сообщение некорректно', reply_markup=keyboard_recommend)


def get_recommendation(message):
    user_id = message.from_user.id
    assert (user_id in user_dict and 'choice' in user_dict[user_id]
            and len(user_dict[user_id]['choice']) != 0), 'List of chosen courses is empty'
    if 'course' not in user_dict[user_id] or 'degree' not in user_dict[user_id]:
        recommendation = ensemble_model.recommend_item_based([4, 1], user_dict[user_id]['choice'],
                                                             course_selector.select())
    else:
        recommendation = ensemble_model.recommend_item_based([4, 1], user_dict[user_id]['choice'],
                                                             course_selector.select(user_dict[user_id]['degree'],
                                                                                    user_dict[user_id]['course']))
    return recommendation


bot.polling(none_stop=True)
