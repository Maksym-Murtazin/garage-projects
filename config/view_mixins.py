from django.db import IntegrityError, transaction


class UniqueConflictFormMixin:
    def form_valid(self, form):
        try:
            with transaction.atomic():
                return super().form_valid(form)
        except IntegrityError:
            # A competing write may have committed since the form was validated.
            form.validate_unique()
            if not form.errors:
                raise
            return self.form_invalid(form)
