from django.contrib import admin

from web.models import NotionDocument
from web.models import Text
from web.services.notion_service.write import scrape
from django.utils.translation import gettext_lazy as _


def scrape_documents(modeladmin, request, queryset):
    for doc in queryset:
        print(doc)
        scrape(doc)


def toggle_bookmark(modeladmin, request, queryset):
    for doc in queryset:
        doc.bookmarked = not doc.bookmarked
        doc.save()


scrape_documents.short_description = "Scrape Notion documents"
toggle_bookmark.short_description = "Toggle bookmark"



class ParentNotionDocumentListFilter(admin.SimpleListFilter):
    title = _("parent")
    parameter_name = "parent_notion_document"

    def lookups(self, request, model_admin):
        return [(x.id, x.title) for x in (NotionDocument.objects.filter(bookmarked=True))]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value():
            return queryset.filter(parent_notion_document_id=self.value())


class NotionDocumentAdmin(admin.ModelAdmin):
    ordering = ("-updated_at",)
    list_display = ["title", "bookmarked", "parent_notion_document", "updated_at"]
    exclude = ("title", "notion_id", "parent_notion_document")
    actions = [scrape_documents, toggle_bookmark]
    list_filter = ("bookmarked", "updated_at", ParentNotionDocumentListFilter)


class TextAdmin(admin.ModelAdmin):
    list_display = ["text", "source_author", "source_series", "source_book", "source_notion_document"]
    list_filter = ("created_at", "updated_at")


admin.site.register(NotionDocument, NotionDocumentAdmin)
admin.site.register(Text, TextAdmin)
