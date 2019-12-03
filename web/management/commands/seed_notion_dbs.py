from django.core.management.base import BaseCommand

from web.models import NotionDatabase


class Command(BaseCommand):
    def handle(self, *args, **options):
        NotionDatabase.objects.create(url="https://www.notion.so/jasonbenn/d7a04baa1cea4dda983747b04ae3ddaa?v=727ed26317ec44caa4c9f2d8393a09b5")
        NotionDatabase.objects.create(url="https://www.notion.so/jasonbenn/2f61537471d64420b40c263ea48ba9e8?v=823167eafe964ed096c24c0a038f5d2c")
        NotionDatabase.objects.create(url="https://www.notion.so/jasonbenn/17213f11f7ef4814b06fe4966f446b91?v=7fee0e1edeb641f3adaebcf2d2e6d31d")
        NotionDatabase.objects.create(url="https://www.notion.so/jasonbenn/130ffb8be05b4d5aaa9445c863760035?v=bced35625f4e4a06a1e82046f763d429")
