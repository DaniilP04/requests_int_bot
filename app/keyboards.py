from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Оставить заявку')],
        [KeyboardButton(text='Мои заявки')],
        [KeyboardButton(text='Помощь')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Выберите пункт в меню..."
)

get_number = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Отправить номер', request_contact=True)]],
    resize_keyboard=True
)

confirm_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Подтвердить')],
        [KeyboardButton(text='Заполнить заново')]
    ],
    resize_keyboard=True
)

no_patronymic_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Нет отчества')]],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Введите отчество или нажмите "Нет отчества"'
)

back_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Назад")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

role_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Сотрудник")],
        [KeyboardButton(text="Школьник")],
        [KeyboardButton(text="Студент")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

staff_departments_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Администрация")],
        [KeyboardButton(text="Пед. состав")],
        [KeyboardButton(text="Тех. персонал")],
        [KeyboardButton(text="Другое")],
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


def build_device_kb(products: list[dict]):
    rows = []
    for product in products:
        rows.append([KeyboardButton(text=product["name"])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def build_bracelet_colors_kb(colors: list[str]):
    keyboard = []
    row = []

    for color in colors:
        row.append(KeyboardButton(text=color))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([KeyboardButton(text="Назад")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_class_number_kb():
    buttons = [
        [InlineKeyboardButton(text=str(i), callback_data=f"class_num_{i}") for i in range(j, min(j + 4, 13))]
        for j in range(1, 13, 4)
    ]
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_school")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_class_letter_kb():
    letters = ["А", "Ә", "Б", "В", "Г", "Ғ", "Д", "Е", "Ë", "Ж", "З", "Ы"]
    letter_buttons = [
        [InlineKeyboardButton(text=letter, callback_data=f"class_letter_{letter}") for letter in letters[i:i+4]]
        for i in range(0, len(letters), 4)
    ]
    letter_buttons.append([InlineKeyboardButton(text='Без литера', callback_data='class_letter_none')])
    letter_buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_class_number")])
    return InlineKeyboardMarkup(inline_keyboard=letter_buttons)


def get_school_type_kb_for_staff():
    buttons = [
        ("Школа", "school_type_школа"),
        ("Гимназия", "school_type_гимназия"),
        ("Лицей", "school_type_лицей"),
        ("Интернат", "school_type_интернат"),
        ("Колледж", "school_type_колледж")
    ]
    kb = InlineKeyboardBuilder()
    for text, callback in buttons:
        kb.button(text=text, callback_data=callback)
    kb.adjust(2)
    return kb.as_markup()


def get_school_type_kb_for_pupil():
    buttons = [
        ("Школа", "school_type_школа"),
        ("Гимназия", "school_type_гимназия"),
        ("Лицей", "school_type_лицей"),
        ("Интернат", "school_type_интернат")
    ]
    kb = InlineKeyboardBuilder()
    for text, callback in buttons:
        kb.button(text=text, callback_data=callback)
    kb.adjust(2)
    return kb.as_markup()


def get_school_type_kb_for_student():
    buttons = [
        ("Колледж", "school_type_колледж")
    ]
    kb = InlineKeyboardBuilder()
    for text, callback in buttons:
        kb.button(text=text, callback_data=callback)
    return kb.as_markup()