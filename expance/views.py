from django.shortcuts import render, redirect
from django.views.generic import ListView
from .models import Expances
from print_funcs import pdf_generator
from django.core.paginator import Paginator

class ExpanceView(ListView):
    template_name = "expances/expances.html"
    model = Expances
    paginate_by = 10
    context_object_name = 'object_list'
    
    def get_queryset(self):
        # Return the base queryset
        return Expances.objects.all()
    
    def get_context_data(self, **kwargs):
        context = {}
        sale_items = Expances.objects.all()
        paginator_sale_items = Paginator(sale_items, self.paginate_by)
        page_number_sale_items = self.request.GET.get('page_sale_items')
        page_obj_sale_items = paginator_sale_items.get_page(page_number_sale_items)
        context = {
            "object_list" : page_obj_sale_items
        }
        return context
    
    def post(self, request):
        queryset = self.get_queryset()
        context = self.get_context_data()
        if 'filtr' in request.POST:
            from_date = request.POST.get('from')
            till_date = request.POST.get('till')
            if from_date and till_date:
                queryset = queryset.filter(date_added__range=[from_date, till_date])
            context["object_list"] = queryset
            return render(request, self.template_name, context)

        elif 'add' in request.POST:
            obj = Expances.objects.create(
                name=request.POST.get("name"),
                amount=request.POST.get("amount"),
                date_added=request.POST.get("date")
            )
            return redirect("expance_app:expance")

        elif 'delete' in request.POST:
            # Handle deleting
            expance_id = request.POST.get('expance')
            Expances.objects.filter(id=expance_id).delete()
            return redirect("expance_app:expance")
        elif 'pdf' in request.POST:
            # Handle PDF generation
            return pdf_generator.generate_pdf(request, queryset)
        return render(request, self.template_name, context)
