from django.contrib import admin
from .models import Child, Resource, Requirement, Allocation

@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'admission_date')
    search_fields = ('name',)
    list_filter = ('age',)

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'quantity', 'unit', 'cost_per_unit')
    list_filter = ('type',)
    search_fields = ('name',)

@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ('resource', 'quantity_per_child', 'frequency')
    list_filter = ('frequency', 'resource__type')

@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = ('child', 'resource', 'quantity', 'date_allocated')
    list_filter = ('date_allocated', 'resource__type')
    search_fields = ('child__name', 'resource__name')