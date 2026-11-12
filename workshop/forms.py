from django import forms

from .models import CarProject, Task


class CarProjectForm(forms.ModelForm):
    class Meta:
        model = CarProject
        fields = ("title", "manufacturer", "model", "year", "description", "status")
        labels = {"model": "Car model", "year": "Production year"}
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}


class TaskFilterForm(forms.Form):
    q = forms.CharField(label="Search tasks", required=False)
    status = forms.ChoiceField(
        choices=[("", "All statuses"), *Task.Status.choices], required=False,
    )
    priority = forms.ChoiceField(
        choices=[("", "All priorities"), *Task.Priority.choices], required=False,
    )
    project = forms.ModelChoiceField(
        queryset=CarProject.objects.all(), empty_label="All projects", required=False,
    )
