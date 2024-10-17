import uuid


def is_uuid(string):
    try:
        uuid_obj = uuid.UUID(string, version=4)
        return True
    except ValueError:
        return False
