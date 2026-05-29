import json
import pprint
from io import BytesIO

import requests
import strapi_api
import redis
from environs import Env
import telebot
from telebot import custom_filters
from telebot import types
from telebot.handler_backends import State, StatesGroup


def connect_to_redis_db(db_name, db_port, db_password):
    redis_db = redis.Redis(
        host=db_name,
        port=db_port,
        username="default",
        password=db_password,
        decode_responses=True
    )
    return redis_db


def run_bot(bot, redis_db, strapi_api_token, host_name):
    
    @bot.message_handler(commands=['start'])
    def start_menu(message):
        fish_list = strapi_api.get_fish(strapi_api_token, host_name)
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
        fish = strapi_api.get_fish(strapi_api_token, host_name, fish_document_id)
        image_url = f"{host_name}{fish.get("picture").get("url")}"
        response = requests.get(image_url)
        response.raise_for_status()
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
        cart_document_id = strapi_api.chek_cart(strapi_api_token, str(call.from_user.id), host_name)
        if not cart_document_id:
            cart_document_id = strapi_api.create_cart(strapi_api_token, str(call.from_user.id), host_name)
        strapi_api.add_fish_to_cart(strapi_api_token, cart_document_id, fish_document_id, host_name)

    
    @bot.callback_query_handler(func=lambda call: call.data == "cart")
    def cart(call):
        cart_document_id = strapi_api.chek_cart(strapi_api_token, str(call.from_user.id), host_name)
        if not cart_document_id:
            cart_document_id = strapi_api.create_cart(strapi_api_token, str(call.from_user.id), host_name)
        redis_db.set(f"cart-{call.from_user.id}", cart_document_id)
        cart_text, cart_fish = strapi_api.get_cart(strapi_api_token, cart_document_id, host_name)
        markup = types.InlineKeyboardMarkup()
        menu_btn = types.InlineKeyboardButton(text="В меню", callback_data="menu")
        pay_btn = types.InlineKeyboardButton(text="Оплатить", callback_data="pay")
        markup.add(menu_btn)
        markup.add(pay_btn)
        if cart_fish:
            for fish in cart_fish:
                rm_btn = types.InlineKeyboardButton(
                    text=f"Удалить {fish.get("title")} из корзины",
                    callback_data=f"rm-{fish.get("documentId")}"
                )
                markup.add(rm_btn)
        if not cart_text:
            bot.send_message(call.message.chat.id, "Ваша корзина пуста", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, cart_text, reply_markup=markup)

    
    @bot.callback_query_handler(func=lambda call: "rm" in call.data)
    def remove_fish(call):
        fish_document_id = call.data.split("-")[1]
        cart_document_id = redis_db.get(f"cart-{call.from_user.id}")
        strapi_api.remove_fish_from_cart(strapi_api_token, cart_document_id, fish_document_id, host_name)
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
        strapi_api.add_email_to_cart(strapi_api_token, cart_document_id, user_email, user_name, host_name)


    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.infinity_polling()


def main():
    env = Env()
    env.read_env()
    strapi_api_token = env.str("STRAPI_API_TOKEN")
    host_name = env.str("HOST")
    db_name = env.str("REDIS_DB")
    db_port = env.str("REDIS_DB_PORT")
    db_password = env.str("REDIS_DB_PASSWORD")
    telegram_bot_api_token = env.str("TELEGRAM_BOT_API_KEY")
    redis_db = connect_to_redis_db(db_name, db_port, db_password)
    bot = telebot.TeleBot(telegram_bot_api_token)
    run_bot(bot, redis_db, strapi_api_token, host_name)


if __name__ == "__main__":
    main()
