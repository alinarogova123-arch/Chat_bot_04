import json
import pprint
from io import BytesIO

import requests
import redis
from environs import Env
import telebot
from telebot import custom_filters
from telebot import types
from telebot.handler_backends import State, StatesGroup


def add_email_to_cart(strapi_api_token, cart_document_id, user_email, user_name):
    headers = {
        "Authorization": f"bearer {strapi_api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "data": {
            "email": user_email,
            "name": user_name,
        }
    }
    url = f"http://localhost:1337/api/carts/{cart_document_id}"
    response = requests.put(url, json=payload, headers=headers)
    response.raise_for_status()



def get_cart(strapi_api_token, cart_document_id):
    headers = {
        "Authorization": f"bearer {strapi_api_token}"
    }
    url = f"http://localhost:1337/api/carts/{cart_document_id}"
    params = {
        "populate": {
            "fish": "title"
        }
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    cart_fish = response.json().get("data").get("fish")
    if not cart_fish:
        return None, None
    cart_text = []
    for fish in cart_fish:
        fish_title = fish.get("title")
        cart_text.append(fish_title)
    cart_text = "\n".join(cart_text)

    return cart_text, cart_fish


def add_fish_to_cart(strapi_api_token, cart_document_id, fish_document_id):
    headers = {
        "Authorization": f"bearer {strapi_api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "data": {
            "fish": {
                "connect": [fish_document_id]
            },
        }
    }
    url = f"http://localhost:1337/api/carts/{cart_document_id}"
    response = requests.put(url, json=payload, headers=headers)
    response.raise_for_status()


def remove_fish_from_cart(strapi_api_token, cart_document_id, fish_document_id):
    headers = {
        "Authorization": f"bearer {strapi_api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "data": {
            "fish": {
                "disconnect": [fish_document_id]
            },
        }
    }
    url = f"http://localhost:1337/api/carts/{cart_document_id}"
    response = requests.put(url, json=payload, headers=headers)
    response.raise_for_status()


def create_cart(strapi_api_token, user_id):
    headers = {
        "Authorization": f"bearer {strapi_api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "data": {
            "tg_id": user_id,
        }
    }
    url = "http://localhost:1337/api/carts"
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    cart_document_id = response.json().get("data").get("documentId")

    return cart_document_id


def connect_to_redis_db(db_name, db_port, db_password):
    redis_db = redis.Redis(
        host=db_name,
        port=db_port,
        username="default",
        password=db_password,
        decode_responses=True
    )
    return redis_db


def get_fish(strapi_api_token, document_id=None):
    headers = {
        "Authorization": f"bearer {strapi_api_token}"
    }
    if document_id:
        url = f"http://localhost:1337/api/fishs/{document_id}?populate[0]=picture"
    else:
        url = "http://localhost:1337/api/fishs"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    fish = response.json().get("data")

    return fish


def chek_cart(strapi_api_token, tg_id):
    headers = {
        "Authorization": f"bearer {strapi_api_token}"
    }
    url = f"http://localhost:1337/api/carts?filters[tg_id][$eq]={tg_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    cart = response.json().get("data")
    if not cart:
        return None
    cart_document_id = response.json().get("data")[0].get("documentId")
    return cart_document_id


def run_bot(bot, redis_db, strapi_api_token):
    
    @bot.message_handler(commands=['start'])
    def start_menu(message):
        fish_list = get_fish(strapi_api_token)
        markup = types.InlineKeyboardMarkup()
        for fish in fish_list:
            fish_btn = types.InlineKeyboardButton(
                text=f"{fish.get("title")}",
                callback_data=f"id-{fish.get("documentId")}"
            )
            markup.add(fish_btn)
        cart_btn = types.InlineKeyboardButton(text="Моя корзина", callback_data="cart")
        markup.add(cart_btn)
        bot.send_message(message.chat.id, "Вебери кнопку", reply_markup=markup)

    
    @bot.callback_query_handler(func=lambda call: "id" in call.data)
    def show_fish(call):
        fish_document_id = call.data.split("-")[1]
        fish = get_fish(strapi_api_token, fish_document_id)
        image_url = f"http://localhost:1337{fish.get("picture").get("url")}"
        response = requests.get(image_url)
        image = BytesIO(response.content)
        markup = types.InlineKeyboardMarkup()
        menu_btn = types.InlineKeyboardButton(text="Назад", callback_data="menu")
        fish_add_btn = types.InlineKeyboardButton(
            text="Добавить в корзину",
            callback_data=f"buy-{fish_document_id}"
        )
        cart_btn = types.InlineKeyboardButton(text="Моя корзина", callback_data="cart")
        markup.add(fish_add_btn)
        markup.add(menu_btn)
        markup.add(cart_btn)
        bot.send_photo(
            chat_id=call.message.chat.id,
            photo=image,
            caption=fish.get("description"),
            reply_markup=markup
        )

    
    @bot.callback_query_handler(func=lambda call: call.data == "menu")
    def back_to_menu(call):
        start_menu(call.message)

    
    @bot.callback_query_handler(func=lambda call: "buy" in call.data)
    def fish_to_buy(call):
        fish_document_id = call.data.split("-")[1]
        cart_document_id = chek_cart(strapi_api_token, str(call.from_user.id))
        if not cart_document_id:
            cart_document_id = create_cart(strapi_api_token, str(call.from_user.id))
        add_fish_to_cart(strapi_api_token, cart_document_id, fish_document_id)

    
    @bot.callback_query_handler(func=lambda call: call.data == "cart")
    def cart(call):
        cart_document_id = chek_cart(strapi_api_token, str(call.from_user.id))
        if not cart_document_id:
            cart_document_id = create_cart(strapi_api_token, str(call.from_user.id))
        redis_db.set(f"cart-{call.from_user.id}", cart_document_id)
        cart_text, cart_fish = get_cart(strapi_api_token, cart_document_id)
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(text="В меню", callback_data="menu")
        btn2 = types.InlineKeyboardButton(text="Оплатить", callback_data="pay")
        markup.add(btn1)
        markup.add(btn2)
        if cart_fish:
            for fish in cart_fish:
                btn = types.InlineKeyboardButton(
                    text=f"Удалить {fish.get("title")} из корзины",
                    callback_data=f"rm-{fish.get("documentId")}"
                )
                markup.add(btn)
        if not cart_text:
            bot.send_message(call.message.chat.id, "Ваша корзина пуста", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, cart_text, reply_markup=markup)

    
    @bot.callback_query_handler(func=lambda call: "rm" in call.data)
    def remove_fish(call):
        fish_document_id = call.data.split("-")[1]
        cart_document_id = redis_db.get(f"cart-{call.from_user.id}")
        remove_fish_from_cart(strapi_api_token, cart_document_id, fish_document_id)
        cart(call)

    
    class UserState(StatesGroup):
        name = State()
        email = State()

    
    @bot.callback_query_handler(func=lambda call: call.data == "pay")
    def get_email(call):   
        bot.send_message(call.message.chat.id, "Укажите ваше имя:")
        bot.set_state(call.from_user.id, UserState.name, call.message.chat.id)

    
    @bot.message_handler(state=UserState.name)
    def waiting_name(message):
        redis_db.set(f"name-{message.from_user.id}", message.text)    
        bot.send_message(message.chat.id, "Укажите ваш email:")
        bot.set_state(message.from_user.id, UserState.email, message.chat.id)
    
    
    @bot.message_handler(state=UserState.email)
    def waiting_email(message):
        redis_db.set(f"email-{message.from_user.id}", message.text)
        user_name = redis_db.get(f"name-{message.from_user.id}")
        user_email = redis_db.get(f"email-{message.from_user.id}")
        cart_document_id = redis_db.get(f"cart-{message.from_user.id}")
        add_email_to_cart(strapi_api_token, cart_document_id, user_email, user_name)


    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.infinity_polling()


def main():
    env = Env()
    env.read_env()
    strapi_api_token = env.str("STRAPI_API_TOKEN")
    db_name = env.str("REDIS_DB")
    db_port = env.str("REDIS_DB_PORT")
    db_password = env.str("REDIS_DB_PASSWORD")
    telegram_bot_api_token = env.str("TELEGRAM_BOT_API_KEY")
    redis_db = connect_to_redis_db(db_name, db_port, db_password)
    bot = telebot.TeleBot(telegram_bot_api_token)
    run_bot(bot, redis_db, strapi_api_token)


if __name__ == "__main__":
    main()
