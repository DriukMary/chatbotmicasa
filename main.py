from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import requests

from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())

genre_to_query = {
    'horor': 'horror',
    'comedy': 'comedy',
    'drama': 'drama',
    'action': 'action',
}

kb_answers = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text='Жахи', callback_data='horor')],
        [types.InlineKeyboardButton(text='Комедія', callback_data='comedy')],
        [types.InlineKeyboardButton(text='Драма', callback_data='drama')],
        [types.InlineKeyboardButton(text='Бойовик', callback_data='action')],
    ]
)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer('Оберіть жанр:', reply_markup=kb_answers)


@dp.message_handler(content_types=types.ContentTypes.STICKER)
async def bot_echo(message: types.Message):
    await message.answer_sticker(f"{message.sticker.file_id}")


def is_genre_callback(c):
    return c.data in genre_to_query.keys()


@dp.callback_query_handler(is_genre_callback)
async def handle_genre_callback(call: types.CallbackQuery):
    genre = call.data
    genre_query = genre_to_query[genre]

    url = f'https://www.omdbapi.com/?apikey=a18b6b6f&s={genre_query}&page=1'
    response = requests.get(url)

    if response.status_code == 200:
        movies = response.json().get('Search', [])[:10]
        message_text = "Оберіть варіант відображення:"
        display_options = types.InlineKeyboardMarkup()
        display_options.row(
            types.InlineKeyboardButton(text='Тільки назви', callback_data=f'display_titles_{genre}'),
            types.InlineKeyboardButton(text='Pазом з роком виходу ', callback_data=f'display_details_{genre}')
        )
        await bot.send_message(call.message.chat.id, message_text, reply_markup=display_options)
    else:
        await bot.send_message(call.message.chat.id, 'API ERROR:' + str(response.status_code))


@dp.callback_query_handler(lambda c: c.data.startswith('display_titles_') or c.data.startswith('display_details_'))
async def handle_display_option_callback(call: types.CallbackQuery):
    display_option, genre = call.data.split('_')[1:]
    genre_query = genre_to_query[genre]

    url = f'https://www.omdbapi.com/?apikey=a18b6b6f&s={genre_query}&page=1'
    response = requests.get(url)

    if response.status_code == 200:
        movies = response.json().get('Search', [])[:10]

        if display_option == 'titles':
            message_text = '\n'.join(f"Title:{movie['Title']}" for movie in movies)
        elif display_option == 'details':
            message_text = '\n\n'.join(f"Title: {movie['Title']}, Year: {movie['Year']}" for movie in movies)

        else:
            message_text = "Невірний варіант відображення."

        await bot.send_message(call.message.chat.id, message_text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
