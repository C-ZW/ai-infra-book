from client import ApiClient


def update_item(client, item_id, data):
    """Update an item by id with the given data dict."""
    return client.patch(f"/items/{item_id}", data)
