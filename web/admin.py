from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from web.models import NotionDatabase
from web.models import NotionDocument
from web.models import Text
from web.services.notion_service.read import get_notion_client
from web.services.notion_service.write import scrape_children
from web.services.notion_service.write import scrape_self


def do_scrape_self(modeladmin, request, queryset):
    for doc in queryset:
        scrape_self(doc)


def do_scrape_children(modeladmin, request, queryset):
    notion_client = get_notion_client()
    for db in queryset:
        scrape_children(db)


do_scrape_self.short_description = "Scrape self"
do_scrape_children.short_description = "Scrape self, children"


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
    actions = [do_scrape_children, do_scrape_self]
    list_filter = ("updated_at",)


class NotionDocumentAdmin(admin.ModelAdmin):
    ordering = ("-updated_at",)
    list_display = ["title", "parent_database", "updated_at"]
    actions = [do_scrape_self]
    list_filter = (ParentNotionDocumentListFilter, "updated_at")


class TextAdmin(admin.ModelAdmin):
    list_display = ["text", "source_author", "source_series", "source_book", "source_notion_document"]
    list_filter = ("created_at", "updated_at")


admin.site.register(NotionDatabase, NotionDatabaseAdmin)
admin.site.register(NotionDocument, NotionDocumentAdmin)
admin.site.register(Text, TextAdmin)
