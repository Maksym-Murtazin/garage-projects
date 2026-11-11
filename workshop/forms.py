from django import forms

from .models import CarProject


class CarProjectForm(forms.ModelForm):
    class Meta:
        model = CarProject
        fields = ("title", "manufacturer", "model", "year", "description", "status")
        labels = {"model": "Car model", "year": "Production year"}
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}
