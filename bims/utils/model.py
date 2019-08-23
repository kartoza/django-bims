def parsing_value_by_type(model, field, value):
    """ parsing value by type of field
    :param model: model that to be saved
    :type model: django.contrib.gis.db.models.model

    :param field: what field to check
    :type field: str

    :param value: value to be parsed
    :type value: str
    """
    if value is None or value == "":
        return None

    # check by type
    field_type = model._meta.get_field(field).get_internal_type()
    if field_type == "IntegerField":
        value = int(float(value))
    elif field_type == "FloatField":
        value = float(value)
    elif field_type == "CharField":
        value = str(value)
    return value
