from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from web.models import NotionDatabase
from web.models import NotionDocument
from web.services.notion_service.write import scrape_children, export_to_anki, export_db_to_anki
from web.services.notion_service.write import scrape_notion_db


def do_scrape_self(modeladmin, request, queryset):
    for doc in queryset:
        scrape_notion_db(doc)


def do_scrape_children(modeladmin, request, queryset):
    for db in queryset:
        scrape_children(db)


def do_export_db_to_anki(modeladmin, request, queryset):
    for db in queryset:
        export_db_to_anki(db)


def do_export_doc_to_anki(modeladmin, request, queryset):
    for db in queryset:
        export_to_anki(db)


do_scrape_self.short_description = "Scrape self"
do_scrape_children.short_description = "Scrape self, children"
do_export_db_to_anki.short_description = "Export to Anki"
do_export_doc_to_anki.short_description = "Export to Anki"


class ParentNotionDocumentListFilter(admin.SimpleListFilter):
    title = _("parent_database")
    parameter_name = "parent_database"

    def lookups(self, request, model_admin):
        return [(x.id, x.title) for x in (NotionDatabase.objects.all())]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(parent_database_id=self.value())


class NotionDatabaseAdmin(admin.ModelAdmin):
    ordering = ("-updated_at",)
    list_display = ["title", "updated_at"]
    exclude = ("title", "notion_id")
    actions = [do_scrape_children, do_scrape_self, do_export_db_to_anki]
    list_filter = ("updated_at",)


class NotionDocumentAdmin(admin.ModelAdmin):
    search_fields = ["title"]
    ordering = ("-updated_at",)
    list_display = ["title", "parent_database", "updated_at"]
    actions = [do_scrape_self, do_export_doc_to_anki]
    list_filter = (ParentNotionDocumentListFilter, "updated_at")


admin.site.register(NotionDatabase, NotionDatabaseAdmin)
admin.site.register(NotionDocument, NotionDocumentAdmin)
