from td_biblio.models import Author
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand



class Command(BaseCommand):
    """
    Fix empty user in the author data for bibliography
    """
    help = "Fix empty author user"

    def handle(self, *args, **options):
        empty_authors = Author.objects.filter(user__isnull=True)
        user_model = get_user_model()
        for author in empty_authors:
            print(author.first_initial, author.last_name, author.id)
            user = user_model.objects.filter(
                first_name__istartswith=author.first_initial,
                last_name__istartswith=author.last_name)
            if user.exists():
                author.user = user[0]
                author.save()
