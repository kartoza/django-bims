from django import forms
from bims.models.harvest_schedule import HarvestSchedule, HarvestPeriod


class HarvestScheduleAdminForm(forms.ModelForm):
    class Meta:
        model = HarvestSchedule
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        period = cleaned.get("period")
        run_at = cleaned.get("run_at")
        dow = (cleaned.get("day_of_week") or "").strip()
        dom = cleaned.get("day_of_month")
        cron = (cleaned.get("cron_expression") or "").strip()
        is_fetching_species = cleaned.get("is_fetching_species")
        parent_species = cleaned.get("parent_species")
        module_group = cleaned.get("module_group")

        # Validate parent species is available when fetching species
        if is_fetching_species:
            has_schedule_parent = parent_species is not None
            has_module_parent = (
                module_group is not None and
                module_group.gbif_parent_species is not None
            )
            if not has_schedule_parent and not has_module_parent:
                self.add_error(
                    "parent_species",
                    "A GBIF parent species is required for species harvests. "
                    "Either set it here or add one to the module group."
                )

        if period in {HarvestPeriod.DAILY, HarvestPeriod.WEEKLY, HarvestPeriod.MONTHLY} and not run_at:
            self.add_error("run_at", "run_at is required for daily/weekly/monthly schedules.")

        if period == HarvestPeriod.WEEKLY and not dow:
            self.add_error("day_of_week", "day_of_week is required for weekly schedules (e.g. 'mon' or '1').")

        if period == HarvestPeriod.MONTHLY and not dom:
            self.add_error("day_of_month", "day_of_month is required for monthly schedules (1–31).")

        if period == HarvestPeriod.CUSTOM:
            if not cron:
                self.add_error("cron_expression", "cron_expression is required for custom schedules.")
            else:
                # Simple validation: 5 space-separated fields of allowed chars
                parts = cron.split()
                if len(parts) != 5:
                    self.add_error("cron_expression", "Cron must have 5 fields: 'm h dom mon dow'.")
                allowed = set("*-/0123456789,")
                for i, p in enumerate(parts):
                    # allow names in DOW (mon-sun) and MON (jan-dec)
                    if i in (3, 4):  # month or dow
                        ok = all(ch.isalpha() or ch in allowed for ch in p.lower())
                    else:
                        ok = all(ch in allowed for ch in p)
                    if not ok:
                        self.add_error("cron_expression", f"Invalid characters in cron field {i+1}: {p}")

        return cleaned
