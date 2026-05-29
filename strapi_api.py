import requests


def add_email_to_cart(strapi_api_token, cart_document_id, user_email, user_name, host_name):
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
    url = f"{host_name}/api/carts/{cart_document_id}"
    response = requests.put(url, json=payload, headers=headers)
    response.raise_for_status()



def get_cart(strapi_api_token, cart_document_id, host_name):
    headers = {
        "Authorization": f"bearer {strapi_api_token}"
    }
    url = f"{host_name}/api/carts/{cart_document_id}"
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


def add_fish_to_cart(strapi_api_token, cart_document_id, fish_document_id, host_name):
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
    url = f"{host_name}/api/carts/{cart_document_id}"
    response = requests.put(url, json=payload, headers=headers)
    response.raise_for_status()


def remove_fish_from_cart(strapi_api_token, cart_document_id, fish_document_id, host_name):
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
    url = f"{host_name}/api/carts/{cart_document_id}"
    response = requests.put(url, json=payload, headers=headers)
    response.raise_for_status()


def create_cart(strapi_api_token, user_id, host_name):
    headers = {
        "Authorization": f"bearer {strapi_api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "data": {
            "tg_id": user_id,
        }
    }
    url = f"{host_name}/api/carts"
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    cart_document_id = response.json().get("data").get("documentId")

    return cart_document_id


def get_fish(strapi_api_token, host_name, document_id=None):
    headers = {
        "Authorization": f"bearer {strapi_api_token}"
    }
    params = {
        "populate": {
            "picture": "url"
        }
    }
    if document_id:
        url = f"{host_name}/api/fishs/{document_id}"
        response = requests.get(url, headers=headers, params=params)
    else:
        url = f"{host_name}/api/fishs"
        response = requests.get(url, headers=headers)
    response.raise_for_status()
    fish = response.json().get("data")

    return fish


def chek_cart(strapi_api_token, user_id, host_name):
    headers = {
        "Authorization": f"bearer {strapi_api_token}"
    }
    params = {
        "filters[tg_id][$eq]": user_id
    }
    url = f"{host_name}/api/carts"
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    cart = response.json().get("data")
    if not cart:
        return None
    cart_document_id = response.json().get("data")[0].get("documentId")
    return cart_document_id
