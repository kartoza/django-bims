import random
from django.conf import settings

PRIMARY = "default"


class PrimaryReplicaRouter:
    def db_for_read(self, model, **hints):
        """
        Reads go to a randomly-chosen replica.
        """
        if settings.REPLICA_ENV_VAR:
            chosen_replica_key = random.choice(
                list(settings.DATABASES.keys())[1:])
            return chosen_replica_key
        else:
            return PRIMARY

    def db_for_write(self, model, **hints):
        """
        Writes always go to primary.
        """
        return PRIMARY

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the primary/replica pool.
        """
        db_set = set(settings.DATABASES.keys())
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        All non-auth models end up in this pool.
        """
        return True
