from django.contrib.admin.models import CHANGE, DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db import transaction


def record_action(actor, target, message, flag=CHANGE):
    LogEntry.objects.create(
        user=actor,
        content_type=ContentType.objects.get_for_model(target),
        object_id=str(target.pk),
        object_repr=str(target)[:200],
        action_flag=flag,
        change_message=message,
    )


class AuditedDeletionMixin:
    def deletion_message(self):
        return "Deleted through the workshop."

    @transaction.atomic
    def form_valid(self, form):
        record_action(self.request.user, self.object, self.deletion_message(), DELETION)
        return super().form_valid(form)
