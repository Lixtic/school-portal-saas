from django.core.management.base import BaseCommand

from academics.ai_tutor import health_check_openai


class Command(BaseCommand):
    help = "Check AI Tutor OpenAI connectivity and basic response path"

    def handle(self, *args, **options):
        result = health_check_openai()

        if result.get("ok"):
            reply = result.get("reply") or "(empty response)"
            self.stdout.write(self.style.SUCCESS(f"AI Tutor check passed. Reply: {reply}"))
            return

        error = result.get("error", "Unknown error")
        self.stderr.write(self.style.ERROR(f"AI Tutor check failed: {error}"))
        raise SystemExit(1)
