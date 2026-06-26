from framework import route, ok, err

DB = {1: {"id": 1, "name": "widget"}, 2: {"id": 2, "name": "gadget"}}


@route("/items/{id}", method="GET")
def get_item(id):
    item = DB.get(id)
    if item is None:
        return err("item {} not found".format(id))
    return ok(item)


@route("/items/{id}", method="DELETE")
def delete_item(id):
    item = DB.pop(id, None)
    if item is None:
        return err("item {} not found".format(id))
    return ok(item)


@route("/items")
def list_items():
    return ok(list(DB.values()))
