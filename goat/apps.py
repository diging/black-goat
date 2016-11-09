from django.apps import AppConfig


class GoatConfig(AppConfig):
    name = 'goat'
    verbose_name = 'Goat'

    def ready(self):
        import goat.signals
        super(GoatConfig, self).ready()
