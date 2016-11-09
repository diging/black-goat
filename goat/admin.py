from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from goat.models import *

class IdentitySystemAdmin(GuardedModelAdmin):
    pass

admin.site.register(IdentitySystem, IdentitySystemAdmin)
