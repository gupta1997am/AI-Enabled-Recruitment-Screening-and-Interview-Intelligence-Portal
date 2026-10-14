from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from .models import Candidate
from .forms import CandidateForm


class CandidateListCBV(LoginRequiredMixin, ListView):
    model = Candidate
    template_name = "recruitment/candidate_list.html"
    context_object_name = "candidates"
    paginate_by = 10
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()

        search = self.request.GET.get("q", "").strip()

        if search:
            from django.db.models import Q

            queryset = queryset.filter(
                Q(candidate_name__icontains=search)
                | Q(email__icontains=search)
                | Q(applied_role__icontains=search)
            )

        return queryset


class CandidateDetailCBV(LoginRequiredMixin, DetailView):
    model = Candidate
    template_name = "recruitment/candidate_detail.html"
    context_object_name = "candidate"


class CandidateCreateCBV(LoginRequiredMixin, CreateView):
    model = Candidate
    form_class = CandidateForm
    template_name = "recruitment/candidate_form.html"
    success_url = reverse_lazy("recruitment:candidate_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Candidate created successfully."
        )
        return super().form_valid(form)


class CandidateUpdateCBV(LoginRequiredMixin, UpdateView):
    model = Candidate
    form_class = CandidateForm
    template_name = "recruitment/candidate_form.html"
    success_url = reverse_lazy("recruitment:candidate_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Candidate updated successfully."
        )
        return super().form_valid(form)


class CandidateDeleteCBV(LoginRequiredMixin, DeleteView):
    model = Candidate
    template_name = "recruitment/candidate_confirm_delete.html"
    success_url = reverse_lazy("recruitment:candidate_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Candidate deleted successfully."
        )
        return super().form_valid(form)