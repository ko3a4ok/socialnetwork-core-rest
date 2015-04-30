from bson import ObjectId, json_util


def wrap(fn):
    def wrapper(obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return fn(obj)
    return wrapper


json_util.default = wrap(json_util.default)
