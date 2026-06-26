from client import ApiClient


def update_item(client, item_id, data):
    return client.patch(f"/items/{item_id}", data)
