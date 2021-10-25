from django.db.models.fields.related import ForeignObjectRel
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db.models import Q


def get_user_from_name(first_name, last_name):
    """
    Get or create a User from first name and last name
    :param first_name: first name of the user
    :param last_name: last name of the user
    :return: User object
    """
    if not first_name:
        return None
    User = get_user_model()
    try:
        if last_name.strip():
            print(last_name)
            user = User.objects.get(
                Q(last_name__iexact=last_name),
                Q(first_name__iexact=first_name) |
                Q(first_name__istartswith=first_name[0])
            )
        else:
            user = User.objects.get(
                Q(first_name__iexact=first_name)
            )
    except User.DoesNotExist:
        username = slugify('{first_name} {last_name}'.format(
            first_name=first_name,
            last_name=last_name
        )).replace('-', '_')
        user, created = User.objects.get_or_create(
            username=username
        )
    except User.MultipleObjectsReturned:
        user = User.objects.filter(
            Q(last_name__iexact=last_name),
            Q(first_name__iexact=first_name) |
            Q(first_name__istartswith=first_name[0])
        )[0]
    user.last_name = last_name[0:30]
    user.first_name = first_name[0:30]
    user.save()
    return user


def get_user(user_name):
    """
    Get or create User object from username
    :param user_name: string of username
    :return: User object
    """
    user_name = user_name.split(' ')
    if len(user_name) > 1:
        last_name = user_name[len(user_name) - 1]
        first_name = ' '.join(user_name[0:len(user_name) - 1])
    else:
        first_name = user_name[0]
        last_name = ''
    first_name = first_name[0:30]
    last_name = last_name[0:30]
    return get_user_from_name(
        first_name,
        last_name
    )


def get_user_reverse(user_name):
    """
    Get or create User object from username
    :param user_name: string of username
    :return: User object
    """
    user_name = user_name.split(', ')
    if len(user_name) > 1:
        first_name = user_name[len(user_name) - 1]
        last_name = ' '.join(user_name[0:len(user_name) - 1])
    else:
        first_name = user_name[0]
        last_name = ''
    first_name = first_name[0:30]
    last_name = last_name[0:30]
    return get_user_from_name(
        first_name,
        last_name
    )


def create_users_from_string(user_string):
    """
    Create user objects from users string.
    e.g. `Tri, Dimas., Bob, Dylan & Jackson, Michael`
    to : [<User>`Dimas Tri`, <User>`Dylan Bob`, <User>`Michael Jackson`]
    :param user_string: string of User(s)
    :return: List of user object
    """
    list_user = []
    if not user_string:
        return list_user
    and_username = ''
    for user_split_1 in user_string.split(','):
        for user_name in user_split_1.split(' and '):
            if '&' in user_name:
                and_username = user_name
                continue
            user = get_user(user_name.strip())
            if user and user not in list_user:
                list_user.append(user)
    if and_username:
        for user_name in and_username.split('&'):
            user = get_user(user_name.strip())
            if user and user not in list_user:
                list_user.append(user)
    return list_user


def merge_users(primary_user, user_list):
    """
    Merge multiple users into one primary_user
    """
    if not primary_user and not user_list:
        return

    print('Merging %s data' % len(user_list))

    User = get_user_model()
    users = User.objects.filter(
        id__in=user_list
    ).exclude(id=primary_user.id)

    links = [
        rel.get_accessor_name() for rel in primary_user._meta.get_fields() if
        issubclass(type(rel), ForeignObjectRel)
    ]

    if links:
        for user in users:
            print('----- {} -----'.format(str(user)))
            for link in links:
                try:
                    objects = getattr(user, link).all()
                    if objects.count() > 0:
                        print('Updating {obj} for : {taxon}'.format(
                            obj=str(objects.model._meta.label),
                            taxon=str(user)
                        ))
                        update_dict = {
                            getattr(user, link).field.name: primary_user
                        }
                        objects.update(**update_dict)
                except Exception as e:  # noqa
                    print(e)
                    continue
            print(''.join(['-' for i in range(len(str(user)) + 12)]))

    users.delete()
