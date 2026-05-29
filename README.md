# Strapi_api.py

Скрипт содержит набор функций для взаимодействия бота со Strapi.

## add_email_to_cart
### Аргументы
+ strapi_api_token - Full access токен Strapi.
+ cart_document_id - `documentId` корзины.
+ user_email - Почта пользователя.
+ user_name - Имя пользователя.
+ host_name - Адрес сервера.

Добавляет имя и почту покупателя, как контактные данные в его корзину.

## get_cart
### Аргументы
+ strapi_api_token - Full access токен Strapi.
+ cart_document_id - `documentId` корзины.
+ host_name - Адрес сервера.

Возращает строку с названиями и массив добавленных в корзину рыб.

## add_fish_to_cart
### Аргументы
+ strapi_api_token - Full access токен Strapi
+ cart_document_id - `documentId` корзины.
+ fish_document_id - `documentId` экземпляра рыбы.
+ host_name - Адрес сервера.

Добавляет рыбу в корзину покупателя.

## remove_fish_from_cart
### Аргументы
+ strapi_api_token - Full access токен Strapi
+ cart_document_id - `documentId` корзины.
+ fish_document_id - `documentId` экземпляра рыбы.
+ host_name - Адрес сервера.

Убирает рыбу из корзины покупателя.

## create_cart
### Аргументы
+ strapi_api_token - Full access токен Strapi
+ user_id - ID пользователя мессенджера.
+ host_name - Адрес сервера.

Создает корзину для покупателя.

## get_fish
### Аргументы
+ strapi_api_token - Full access токен Strapi
+ host_name - Адрес сервера.
+ document_id - Необязательный аргумент, `documentId` экземпляра рыбы.

Возвращает массив со всеми экземплярами рыбы из модели Fish или конкретный экземляр, если передан аргумент document_id
(значение ключа `documentId` из конкретного экземпляра).

## chek_cart
### Аргументы
+ strapi_api_token - Full access токен Strapi.
+ user_id - ID пользователя мессенджера.
+ host_name - Адрес сервера.

Проверяет существует ли корзина по ID пользователя мессенджера, возвращает `documentId` корзины, либо `None`,
если корзина еще не создана.

