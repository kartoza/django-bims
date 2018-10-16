
def remove_params_from_uri(params, uri):
    formatted_uri = uri
    for param in params:
        # remove zoom value from uri
        param_string = param + '='
        param_char = ''
        param_index = formatted_uri.find(param_string)
        param_value = ''
        param_value_index = 0

        while param_char != '&':
            pre_param_value_index = 0
            if param_value_index > 0:
                pre_param_value_index = param_value_index - 1

            param_char = formatted_uri[
                        param_index +
                        len(param_string) +
                        pre_param_value_index:
                        param_index +
                        len(param_string) +
                        param_value_index]

            param_value_index += 1
            if param_char and param_char != '&':
                param_value += param_char

        formatted_uri = formatted_uri.replace(
                param_string + param_value,
                param_string)
    return formatted_uri
