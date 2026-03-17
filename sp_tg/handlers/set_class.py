"""Предоставляет возможного изменять класс пользователя.

Когда вы хотите получить расписание, то неявно имеете ввиду что хотите
получить расписание для своего класса.
Это и называется классом по умолчанию.
"""

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from sp.db import User
from sp.view.messages import MessagesView
from sp_tg.filters import IsAdmin
from sp_tg.keyboards import PASS_SET_CL_MARKUP, get_main_keyboard
from sp_tg.messages import SET_CLASS_MESSAGE, get_home_message

router = Router(name=__name__)

# Статические клавиатуры при выборе класса
# pass => Пропустить смену класс и установить None
# cl_features => Список преимуществ если указать класс
BACK_SET_CL_MARKUP = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="◁", callback_data="set_class"),
            InlineKeyboardButton(text="Без класса", callback_data="pass"),
        ]
    ]
)


# Какие преимущества получает указавшие класс пользователь
# Это сообщение должно побуждать пользователей указывать свой класс
# по умолчанию чтобы получать преимущества
CL_FEATURES_MESSAGE = (
    "🌟 Если вы укажете класс, то сможете:"
    "\n\n-- Быстро получать расписание для класса, кнопкой в главном меню."
    '\n-- Не указывать ваш класс в текстовых запросах (прим. "пн").'
    "\n-- Получать уведомления и рассылку расписания для класса."
    "\n-- Просматривать список изменений для вашего класса."
    "\n-- Использовать счётчик cl/lessons."
    "\n\n💎 Список возможностей может пополняться."
)


# Описание команд
# ===============


@router.message(Command("cl_features"))
async def restrictions_handler(message: Message) -> None:
    """Отправляет список преимуществ при указанном классе."""
    await message.answer(text=CL_FEATURES_MESSAGE)


@router.message(Command("set_class"), IsAdmin())
async def set_class_command(
    message: Message,
    user: User,
    command: CommandObject,
    view: MessagesView,
) -> None:
    """Изменяет класс или удаляет данные о пользователе.

    - Если такого класса не существует, показывает список доступных
      классов.
    - Указывать класс можно передавая его как аргумент.
    - Если не указывать класс, сбрасывает данные пользователя и
      переводит его в состояние выбора класса.
    """
    # Если указали класс в команде
    if command.args is not None:
        if await user.set_cl(command.args, view.sc):
            await message.answer(
                text=get_home_message(command.args),
                reply_markup=get_main_keyboard(
                    command.args, view.relative_day(user)
                ),
            )
        # Если такого класса не существует
        else:
            text = "👀 Такого класса не существует."
            text += f"\n💡 Доступные классы: {', '.join(view.sc.lessons)}"
            await message.answer(text=text)

    # Сбрасываем пользователя и переводим в состояние выбора класса
    else:
        await user.unset_cl()
        await message.answer(
            text=SET_CLASS_MESSAGE, reply_markup=PASS_SET_CL_MARKUP
        )


@router.message(Command("pass"), IsAdmin())
async def pass_handler(message: Message, view: MessagesView, user: User) -> None:
    """Отвязывает пользователя от класса по умолчанию.

    Если более конкретно, то устанавливает класс пользователя в
    None и отправляет главное сообщение и клавиатуру.
    """
    await user.set_cl("", view.sc)
    await message.answer(
        text=get_home_message(user.cl),
        reply_markup=get_main_keyboard(user.cl, None),
    )


# Обработчики Callback клавиатуры
# ===============================


@router.callback_query(F.data == "cl_features")
async def cl_features_callback(query: CallbackQuery) -> None:
    """Отправляет сообщения с преимуществами указанного класса."""
    await query.message.edit_text(
        text=CL_FEATURES_MESSAGE, reply_markup=BACK_SET_CL_MARKUP
    )


@router.callback_query(F.data == "set_class", IsAdmin())
async def set_class_callback(query: CallbackQuery, user: User) -> None:
    """Сбрасывает класс пользователя.

    Сбрасывает данные пользователя и переводит в состояние выбора
    класса по умолчанию.
    """
    await user.unset_cl()
    await query.message.edit_text(
        text=SET_CLASS_MESSAGE, reply_markup=PASS_SET_CL_MARKUP
    )


@router.callback_query(F.data == "pass", IsAdmin())
async def pass_class_callback(
    query: CallbackQuery, view: MessagesView, user: User
) -> None:
    """Отвязывает пользователя от класса.

    Как и в случае с командой /pass.
    Просто устанавливает класс пользователя в None и отправляет
    главное сообщение с основной клавиатурой бота.
    """
    await user.set_cl("", view.sc)
    await query.message.edit_text(
        text=get_home_message(user.cl),
        reply_markup=get_main_keyboard(user.cl, None),
    )
