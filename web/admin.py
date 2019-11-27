from django.contrib import admin

from web.models import NotionDocument


def scrape_documents(modeladmin, request, queryset):
    for doc in queryset:
        print(doc)

scrape_documents.short_description = "Scrape Notion documents"


class NotionDocumentAdmin(admin.ModelAdmin):
    exclude = ("title", "notion_id")
    actions = [scrape_documents]


admin.site.register(NotionDocument, NotionDocumentAdmin)
