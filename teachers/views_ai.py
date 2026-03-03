from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def aura_interaction_view(request):
    """
    Render the Aura command center page.
    """
    return render(request, 'teachers/ai_sessions_list.html')
