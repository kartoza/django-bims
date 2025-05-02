import subprocess
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Runs Grunt tasks, then builds with Webpack in production mode,
    and finally runs collectstatic.
    """

    help = "Run Grunt, Webpack production build, and then collectstatic."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('>>> Starting Grunt tasks...'))
        subprocess.check_call(
            ['grunt', '--gruntfile=/Gruntfile.js', '--base=/'],
            shell=True
        )

        self.stdout.write(self.style.SUCCESS('>>> Running Webpack in production mode (bims folder)...'))
        subprocess.check_call(
            ['webpack', '--mode', 'production', '--config', 'webpack.config.js'],
            shell=True,
            cwd='bims'
        )

        self.stdout.write(self.style.SUCCESS('>>> Collecting static files...'))
        call_command('collectstatic', verbosity=0, interactive=False)

        self.stdout.write(self.style.SUCCESS('>>> All tasks completed successfully!'))
