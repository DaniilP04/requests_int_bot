from aiogram import F, Router
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.database import db
import app.keyboards as kb

router = Router()


class Register(StatesGroup):
    role = State()
    surname = State()
    name = State()
    patronymic = State()
    school = State()
    class_number = State()
    class_letter = State()
    class_name = State()
    staff_department = State()
    number = State()
    device_type = State()
    bracelet_color = State()
    confirm = State()


def normalize_spaces(value: str) -> str:
    return " ".join((value or "").strip().split())


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        'Здравствуйте! Спасибо за обращение в Компанию Интегро!',
        reply_markup=kb.main
    )


@router.message(Command('help'))
async def cmd_help_command(message: Message):
    await message.answer('Нажмите на кнопку "Оставить заявку", чтобы подать заявку.')


@router.message(F.text == "Помощь")
async def cmd_help(message: Message):
    await message.answer(
        "Дополнительную информацию можно узнать по телефону +77051784114 или написать @Danya555666."
    )


@router.message(F.text == "Мои заявки")
async def my_requests(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    requests = await db.check_by_telegram_id(telegram_id)

    if not requests:
        await message.answer("У вас нет заявок.")
        return

    msg = "Ваши заявки:\n\n"
    for req in requests:
        msg += (
            f"Устройство: *{req['device_type']}*\n"
            f"Трек: `{req['track_id']}`\n"
            f"Пароль: `{req['password']}`\n"
            f"Статус: *{req['status']}*\n\n"
        )

    await message.answer(msg, parse_mode="Markdown")


@router.message(F.text == 'Оставить заявку')
async def register(message: Message, state: FSMContext):
    await state.set_state(Register.role)
    await message.answer("Выберите вашу роль:", reply_markup=kb.role_kb)


@router.message(Register.role)
async def process_role(message: Message, state: FSMContext):
    role = (message.text or "").strip()
    if role not in ["Сотрудник", "Школьник", "Студент"]:
        await message.answer("Пожалуйста, выберите одну из кнопок ниже.")
        return

    await state.update_data(role=role)
    await state.set_state(Register.surname)
    await message.answer("Введите вашу фамилию:", reply_markup=ReplyKeyboardRemove())


@router.message(Register.surname)
async def get_surname(message: Message, state: FSMContext):
    await state.update_data(surname=normalize_spaces(message.text))
    await state.set_state(Register.name)
    await message.answer('Введите ваше имя')


@router.message(Register.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=normalize_spaces(message.text))
    await state.set_state(Register.patronymic)
    await message.answer(
        'Введите ваше отчество (если нет — нажмите кнопку ниже)',
        reply_markup=kb.no_patronymic_kb
    )


@router.message(Register.patronymic)
async def register_fullname(message: Message, state: FSMContext):
    patronymic = normalize_spaces(message.text)
    data = await state.get_data()

    full_name = f"{data['surname']} {data['name']}"
    if patronymic != "Нет отчества":
        full_name += f" {patronymic}"

    await state.update_data(full_name=normalize_spaces(full_name))
    await state.set_state(Register.school)

    role = data.get("role")

    if role == "Сотрудник":
        kb_for_role = kb.get_school_type_kb_for_staff()
    elif role == "Школьник":
        kb_for_role = kb.get_school_type_kb_for_pupil()
    elif role == "Студент":
        kb_for_role = kb.get_school_type_kb_for_student()
    else:
        await message.answer("Неизвестная роль. Попробуйте сначала.")
        return

    await message.answer(
        "Отлично, переходим далее.",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer("Выберите тип учебного заведения:", reply_markup=kb_for_role)


@router.callback_query(F.data.startswith("school_type_"))
async def choose_school_type(callback: CallbackQuery, state: FSMContext):
    school_type = callback.data.split("_", 2)[-1]
    await state.update_data(school_type=school_type)

    schools = await db.get_schools_by_type(school_type)
    if not schools:
        await callback.message.edit_text("Нет заведений такого типа.")
        return

    school_list = "\n".join([f"{row['id']}: {row['name']}" for row in schools])

    await state.set_state(Register.school)
    await callback.message.edit_text(
        f"Вы выбрали: {school_type.title()}\n\n"
        f"Теперь введите ID учебного заведения из списка ниже:\n\n{school_list}"
    )
    await callback.message.answer(
        "Если хотите вернуться, нажмите кнопку Назад.",
        reply_markup=kb.back_kb
    )


@router.message(Register.school)
async def register_school_by_id(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.update_data(school_type=None, school=None)
        role_data = await state.get_data()
        role = role_data.get("role")

        if role == "Сотрудник":
            markup = kb.get_school_type_kb_for_staff()
        elif role == "Школьник":
            markup = kb.get_school_type_kb_for_pupil()
        elif role == "Студент":
            markup = kb.get_school_type_kb_for_student()
        else:
            markup = kb.get_school_type_kb_for_pupil()

        await state.set_state(Register.school)
        await message.answer("Выберите тип учебного заведения:", reply_markup=markup)
        return

    try:
        school_id = int((message.text or "").strip())
    except ValueError:
        await message.answer("Введите корректный ID (только число).", reply_markup=kb.back_kb)
        return

    school = await db.get_school_by_id(school_id)
    if not school:
        await message.answer("Заведение не найдено. Попробуйте снова.", reply_markup=kb.back_kb)
        return

    await state.update_data(school=school["name"])
    role_data = await state.get_data()
    role = role_data.get("role")

    if role == "Студент":
        await state.set_state(Register.class_name)
        await message.answer(
            f"Вы выбрали: {school['name']}\n\nВведите название вашей учебной группы:",
            reply_markup=kb.back_kb
        )
    elif role == "Сотрудник":
        await state.set_state(Register.staff_department)
        await message.answer(
            f"Вы выбрали: {school['name']}\n\nВыберите подразделение:",
            reply_markup=kb.staff_departments_kb
        )
    else:
        await state.set_state(Register.class_number)
        await message.answer(
            f"Вы выбрали: {school['name']}\n\nТеперь выберите номер класса:",
            reply_markup=kb.get_class_number_kb()
        )


@router.message(Register.class_name)
async def class_name_handler(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.update_data(school_type=None, school=None)
        role_data = await state.get_data()
        role = role_data.get("role")

        if role == "Сотрудник":
            markup = kb.get_school_type_kb_for_staff()
        elif role == "Школьник":
            markup = kb.get_school_type_kb_for_pupil()
        elif role == "Студент":
            markup = kb.get_school_type_kb_for_student()
        else:
            markup = kb.get_school_type_kb_for_pupil()

        await state.set_state(Register.school)
        await message.answer("Выберите тип учебного заведения:", reply_markup=markup)
        return

    group_name = normalize_spaces(message.text)
    if not group_name:
        await message.answer("Введите корректное название группы или нажмите 'Назад'.", reply_markup=kb.back_kb)
        return

    await state.update_data(class_name=group_name)
    await state.set_state(Register.number)
    await message.answer(
        f"Вы выбрали группу: {group_name}\nПожалуйста, отправьте ваш номер телефона:",
        reply_markup=kb.get_number
    )


@router.message(Register.staff_department)
async def staff_department_handler(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.set_state(Register.school)
        await message.answer("Введите ID учебного заведения снова:", reply_markup=kb.back_kb)
        return

    department = (message.text or "").strip()
    valid_departments = ["Администрация", "Пед. состав", "Тех. персонал", "Другое"]

    if department not in valid_departments:
        await message.answer("Пожалуйста, выберите подразделение кнопками ниже.", reply_markup=kb.staff_departments_kb)
        return

    await state.update_data(class_name=f"Сотрудник: {department}")
    await state.set_state(Register.number)
    await message.answer(
        f"Подразделение сохранено: {department}\nПожалуйста, отправьте ваш номер телефона:",
        reply_markup=kb.get_number
    )


@router.callback_query(F.data.startswith("class_num_"))
async def process_class_number(callback: CallbackQuery, state: FSMContext):
    class_num = callback.data.split("_")[-1]
    await state.update_data(class_number=class_num)
    await state.set_state(Register.class_letter)

    await callback.message.edit_text(
        f"Вы выбрали класс: {class_num}\nТеперь выберите литеру (букву) класса:",
        reply_markup=kb.get_class_letter_kb()
    )


@router.callback_query(F.data.startswith("class_letter_"))
async def process_class_letter(callback: CallbackQuery, state: FSMContext):
    letter = callback.data.split("_")[-1]
    if letter == "none":
        letter = ""

    data = await state.get_data()
    class_full = f"{data['class_number']}"
    if letter:
        class_full += f"{letter}"

    await state.update_data(class_name=class_full)
    await state.set_state(Register.number)

    await callback.message.edit_text(f"Класс сохранён: {class_full}")
    await callback.message.answer(
        "Пожалуйста, отправьте ваш номер телефона:",
        reply_markup=kb.get_number
    )


@router.message(Register.number, F.contact)
async def register_number(message: Message, state: FSMContext):
    await state.update_data(number=message.contact.phone_number)

    products = await db.get_public_products()
    if not products:
        await message.answer(
            "Сейчас нет доступных устройств. Попробуйте позже.",
            reply_markup=kb.main
        )
        await state.clear()
        return

    await state.update_data(products=products)
    await state.set_state(Register.device_type)

    photo = FSInputFile("images/devices.jpg")
    await message.answer_photo(photo, caption="Вот как выглядят устройства:")

    product_lines = [f"- {product['name']} ({product['price']} тг)" for product in products]
    products_text = "\n".join(product_lines)

    await message.answer(
        f"Что вы хотите заказать?\n\n{products_text}",
        reply_markup=kb.build_device_kb(products)
    )


@router.message(Register.device_type)
async def device_type_selected(message: Message, state: FSMContext):
    if message.text == "Назад":
        data = await state.get_data()
        role = data.get("role")

        if role == "Студент":
            await state.set_state(Register.class_name)
            await message.answer("Введите название вашей группы:", reply_markup=kb.back_kb)
        elif role == "Сотрудник":
            await state.set_state(Register.staff_department)
            await message.answer("Выберите подразделение:", reply_markup=kb.staff_departments_kb)
        else:
            await state.set_state(Register.class_number)
            await message.answer("Выберите номер класса:", reply_markup=kb.get_class_number_kb())
        return

    selected_name = normalize_spaces(message.text)
    data = await state.get_data()
    products = data.get("products") or await db.get_public_products()

    available_names = [product["name"] for product in products]
    if selected_name not in available_names:
        await message.answer("Пожалуйста, выберите одно из доступных устройств.", reply_markup=kb.build_device_kb(products))
        return

    if selected_name == "Браслет":
        bracelet = next((product for product in products if product["name"] == "Браслет"), None)
        colors = bracelet["colors"] if bracelet else []

        if not colors:
            await message.answer("Сейчас нет доступных цветов браслета. Выберите другое устройство.")
            return

        await state.update_data(device_type="Браслет")
        await state.set_state(Register.bracelet_color)
        await message.answer("Выберите цвет браслета:", reply_markup=kb.build_bracelet_colors_kb(colors))
        return

    await state.update_data(device_type=selected_name)
    await state.set_state(Register.confirm)

    data = await state.get_data()
    await message.answer(
        f"Проверьте вашу заявку:\n\n"
        f"ФИО: {data['full_name']}\n"
        f"Учебное заведение: {data['school']}\n"
        f"Класс / группа / подразделение: {data['class_name']}\n"
        f"Телефон: {data['number']}\n"
        f"Устройство: {data['device_type']}",
        reply_markup=kb.confirm_kb
    )


@router.message(Register.bracelet_color)
async def bracelet_color_selected(message: Message, state: FSMContext):
    if message.text == "Назад":
        data = await state.get_data()
        products = data.get("products") or await db.get_public_products()
        await state.set_state(Register.device_type)
        await message.answer("Выберите устройство:", reply_markup=kb.build_device_kb(products))
        return

    color = normalize_spaces(message.text)
    data = await state.get_data()
    products = data.get("products") or await db.get_public_products()

    bracelet = next((product for product in products if product["name"] == "Браслет"), None)
    valid_colors = bracelet["colors"] if bracelet else []

    if color not in valid_colors:
        await message.answer(
            "Пожалуйста, выберите цвет браслета, используя кнопки ниже.",
            reply_markup=kb.build_bracelet_colors_kb(valid_colors)
        )
        return

    await state.update_data(device_type=f"Браслет ({color})")
    await state.set_state(Register.confirm)

    data = await state.get_data()
    await message.answer(
        f"Проверьте вашу заявку:\n\n"
        f"ФИО: {data['full_name']}\n"
        f"Учебное заведение: {data['school']}\n"
        f"Класс / группа / подразделение: {data['class_name']}\n"
        f"Телефон: {data['number']}\n"
        f"Устройство: {data['device_type']}",
        reply_markup=kb.confirm_kb
    )


@router.message(Register.confirm, F.text == 'Подтвердить')
async def confirm_submission(message: Message, state: FSMContext):
    data = await state.get_data()

    is_duplicate = await db.is_duplicate_request(
        data['full_name'],
        data['school'],
        data['class_name']
    )

    if is_duplicate:
        await message.answer(
            "Похоже, у вас уже есть активная заявка с такими данными.\n"
            "Повторно подавать заявку не нужно.",
            reply_markup=kb.main
        )
        await state.clear()
        return

    result = await db.add_request(
        full_name=data['full_name'],
        school=data['school'],
        class_name=data['class_name'],
        phone=data['number'],
        device_type=data['device_type'],
        telegram_id=message.from_user.id
    )

    await message.answer(
        f"Заявка отправлена!\n\n"
        f"Ваш трек-номер: {result['track_id']}\n"
        f"Ваш пароль: {result['password']}\n\n"
        f"Чтобы узнать статус, нажмите «Мои заявки» в меню.\n"
        f"Дополнительную информацию можно узнать по телефону +77051784114 или написать @Danya555666.",
        reply_markup=kb.main
    )
    await state.clear()


@router.message(Register.confirm, F.text == 'Заполнить заново')
async def restart_submission(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Register.role)
    await message.answer(
        "Хорошо, начнем заново. Выберите вашу роль:",
        reply_markup=kb.role_kb
    )


@router.callback_query(F.data == "back_to_school")
async def back_to_school(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    role = data.get("role")

    if role == "Сотрудник":
        markup = kb.get_school_type_kb_for_staff()
    elif role == "Школьник":
        markup = kb.get_school_type_kb_for_pupil()
    elif role == "Студент":
        markup = kb.get_school_type_kb_for_student()
    else:
        markup = kb.get_school_type_kb_for_pupil()

    await state.set_state(Register.school)
    await callback.message.edit_text(
        "Выберите тип учебного заведения:",
        reply_markup=markup
    )


@router.callback_query(F.data == "back_to_class_number")
async def back_to_class_number(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Register.class_number)
    await callback.message.edit_text(
        "Выберите номер класса:",
        reply_markup=kb.get_class_number_kb()
    )