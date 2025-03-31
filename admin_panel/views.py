# admin_panel/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDay, ExtractHour
from django.utils import timezone
from .models import FAQ, QueryLog
from .forms import FAQForm


@login_required
def dashboard_view(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    query_type = request.GET.get('query_type', 'all')
    top_n = request.GET.get('top_n', '10')

    # Base query filter for date range
    query_filter = Q()
    if start_date:
        start_datetime = timezone.datetime.strptime(start_date, '%Y-%m-%d').replace(
            tzinfo=timezone.get_current_timezone())
        query_filter &= Q(timestamp__gte=start_datetime)
    if end_date:
        end_datetime = timezone.datetime.strptime(end_date, '%Y-%m-%d').replace(
            hour=23, minute=59, second=59, tzinfo=timezone.get_current_timezone())
        query_filter &= Q(timestamp__lte=end_datetime)

    # Apply query type filter
    if query_type == 'resolved':
        query_filter &= Q(unresolved=False)
    elif query_type == 'unresolved':
        query_filter &= Q(unresolved=True)

    # Core metrics (adjusted to respect query_type filter)
    total_queries = QueryLog.objects.filter(query_filter).count()
    unresolved_queries = QueryLog.objects.filter(query_filter & Q(unresolved=True)).count()
    resolution_rate = ((total_queries - unresolved_queries) / total_queries * 100) if total_queries > 0 else 0
    avg_response_time = QueryLog.objects.filter(query_filter).aggregate(avg_time=Avg('response_time'))['avg_time'] or 0
    peak_hour = QueryLog.objects.filter(query_filter).annotate(hour=ExtractHour('timestamp')).values('hour').annotate(
        count=Count('id')).order_by('-count').first()
    leads = QueryLog.objects.filter(query_filter & Q(is_lead=True)).count()

    # Query stats for bar chart
    # Show all queries for resolved/unresolved, limit to top_n only for 'all'
    query_stats_base = QueryLog.objects.filter(query_filter).values('query_text').annotate(count=Count('id')).order_by(
        '-count')
    if query_type == 'all':
        if top_n == 'all':
            query_stats = query_stats_base  # No limit when top_n is 'all'
        else:
            query_stats = query_stats_base[:int(top_n)]  # Limit to top_n for numeric values
    else:
        query_stats = query_stats_base  # No limit for resolved/unresolved

    # Time stats for line chart (queries per day, respects query_type)
    time_stats = QueryLog.objects.filter(query_filter).annotate(day=TruncDay('timestamp')).values('day').annotate(
        count=Count('id')).order_by('day')

    context = {
        'total_queries': total_queries,
        'unresolved_queries': unresolved_queries,
        'resolution_rate': round(resolution_rate, 2),
        'avg_response_time': round(avg_response_time, 2),
        'peak_hour': peak_hour['hour'] if peak_hour else 'N/A',
        'leads': leads,
        'query_stats': query_stats,
        'time_stats': list(time_stats),
        'query_type': query_type,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
def manage_faqs(request):
    if request.method == 'POST':
        form = FAQForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_panel:manage_faqs')
    else:
        form = FAQForm()

    faqs = FAQ.objects.all()
    return render(request, 'admin_panel/manage_faqs.html', {'faqs': faqs, 'form': form})


@login_required
def edit_faq(request, faq_id):
    faq = get_object_or_404(FAQ, id=faq_id)
    if request.method == 'POST':
        form = FAQForm(request.POST, instance=faq)
        if form.is_valid():
            form.save()
            return redirect('admin_panel:manage_faqs')
        return render(request, 'admin_panel/edit_faq.html', {'form': form, 'faq': faq})
    else:
        form = FAQForm(instance=faq)
    return render(request, 'admin_panel/edit_faq.html', {'form': form, 'faq': faq})


@login_required
def delete_faq(request, faq_id):
    faq = get_object_or_404(FAQ, id=faq_id)
    if request.method == 'POST':
        faq.delete()
    return redirect('admin_panel:manage_faqs')