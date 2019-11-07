from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from goat.models import *


class IdentitySystemAdmin(GuardedModelAdmin):
    pass


class IdentityAdmin(GuardedModelAdmin):
    pass


class ConceptAdmin(GuardedModelAdmin):
    pass


class AuthorityAdmin(GuardedModelAdmin):
    pass

class SearchResultAdmin(GuardedModelAdmin):
    pass

admin.site.register(IdentitySystem, IdentitySystemAdmin)
admin.site.register(Identity, IdentityAdmin)
admin.site.register(Concept, ConceptAdmin)
admin.site.register(Authority, AuthorityAdmin)
admin.site.register(SearchResultSet, SearchResultAdmin)
