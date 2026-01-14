from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import Expense, Asset, Vendor
from .forms import ExpenseForm, VendorForm, AssetForm

@login_required
def dashboard(request):
    if request.user.user_type != 'admin':
        messages.error(request, "Access Denied")
        return redirect('dashboard')
        
    total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    recent_expenses = Expense.objects.select_related('category').order_by('-date')[:5]
    asset_count = Asset.objects.count()
    vendor_count = Vendor.objects.count()
    
    context = {
        'total_expenses': total_expenses,
        'recent_expenses': recent_expenses,
        'asset_count': asset_count,
        'vendor_count': vendor_count
    }
    return render(request, 'business/dashboard.html', context)

@login_required
def expense_list(request):
    expenses = Expense.objects.select_related('category', 'vendor').order_by('-date')
    return render(request, 'business/expense_list.html', {'expenses': expenses})

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.approved_by = request.user
            expense.save()
            messages.success(request, "Expense recorded successfully")
            return redirect('business:expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'business/form_base.html', {'form': form, 'title': 'Add New Expense'})

@login_required
def asset_list(request):
    assets = Asset.objects.all().order_by('category')
    return render(request, 'business/asset_list.html', {'assets': assets})
