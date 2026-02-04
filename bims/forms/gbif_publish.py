from django import forms
from bims.models.gbif_publish import GbifPublish, PublishPeriod


class GbifPublishAdminForm(forms.ModelForm):
    class Meta:
        model = GbifPublish
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        period = cleaned.get("period")
        run_at = cleaned.get("run_at")
        dow = (cleaned.get("day_of_week") or "").strip()
        dom = cleaned.get("day_of_month")
        cron = (cleaned.get("cron_expression") or "").strip()

        if period in {PublishPeriod.DAILY, PublishPeriod.WEEKLY, PublishPeriod.MONTHLY} and not run_at:
            self.add_error("run_at", "run_at is required for daily/weekly/monthly schedules.")

        if period == PublishPeriod.WEEKLY and not dow:
            self.add_error("day_of_week", "day_of_week is required for weekly schedules (e.g. 'mon' or '1').")

        if period == PublishPeriod.MONTHLY and not dom:
            self.add_error("day_of_month", "day_of_month is required for monthly schedules (1–31).")

        if period == PublishPeriod.CUSTOM:
            if not cron:
                self.add_error("cron_expression", "cron_expression is required for custom schedules.")
            else:
                parts = cron.split()
                if len(parts) != 5:
                    self.add_error("cron_expression", "Cron must have 5 fields: 'm h dom mon dow'.")
                allowed = set("*-/0123456789,")
                for i, p in enumerate(parts):
                    if i in (3, 4):
                        ok = all(ch.isalpha() or ch in allowed for ch in p.lower())
                    else:
                        ok = all(ch in allowed for ch in p)
                    if not ok:
                        self.add_error("cron_expression", f"Invalid characters in cron field {i+1}: {p}")

        return cleaned
