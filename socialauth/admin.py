from django.contrib import admin
from django.db.models import Model
from socialauth import models

for name in dir(models):
    item = getattr(models, name)
    if isinstance(item, type) and issubclass(item, Model):
        try:
            admin.site.register(item)
        except admin.sites.AlreadyRegistered:
            pass
