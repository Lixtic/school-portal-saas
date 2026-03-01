with open('students/views_ai.py', 'a', encoding='utf-8') as f:
    f.write('''

from academics.models import StudyGroupRoom, StudyGroupMessage, StudentXP

@login_required
def aura_arena_view(request):
    if request.user.user_type != 'student':
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "Only students can enter the Aura Arena.")
        return redirect('dashboard')
    
    from students.models import Student
    student = Student.objects.filter(user=request.user).first()
    if not student or not student.current_class:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.warning(request, "You must be assigned to a class to enter.")
        return redirect('dashboard')
        
    room, _ = StudyGroupRoom.objects.get_or_create(
        student_class=student.current_class,
        defaults={'name': f"{student.current_class.name} Arena"}
    )
    
    xp_profile, _ = StudentXP.objects.get_or_create(student=student)
    
    from django.shortcuts import render
    context = {
        'room': room,
        'student': student,
        'xp': xp_profile
    }
    return render(request, 'students/aura_arena.html', context)


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def aura_arena_api(request):
    import json
    from django.http import JsonResponse
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    from students.models import Student
    student = Student.objects.filter(user=request.user).first()
    if not student or not student.current_class:
        return JsonResponse({'error': 'No class assigned'}, status=400)
        
    room = StudyGroupRoom.objects.filter(student_class=student.current_class).first()
    if not room:
        return JsonResponse({'error': 'No room found'}, status=404)
        
    if request.method == 'GET':
        last_id = int(request.GET.get('last_id', 0))
        msgs = StudyGroupMessage.objects.filter(room=room, id__gt=last_id).order_by('created_at')
        
        data = []
        for m in msgs:
            data.append({
                'id': m.id,
                'content': m.content,
                'sender': m.sender.get_full_name() if m.sender else 'Aura',
                'is_aura': m.is_aura,
                'is_battle': m.is_battle_question,
                'battle_answered': m.battle_answered,
                'winner': m.battle_winner.get_full_name() if m.battle_winner else None,
                'time': m.created_at.strftime('%H:%M'),
                'is_me': m.sender == request.user if m.sender else False
            })
        return JsonResponse({'messages': data})

    elif request.method == 'POST':
        payload = json.loads(request.body)
        content = payload.get('content', '').strip()
        if not content:
            return JsonResponse({'error': 'Empty message'}, status=400)
            
        active_battle = StudyGroupMessage.objects.filter(room=room, is_battle_question=True, battle_answered=False).last()
        
        msg = StudyGroupMessage.objects.create(room=room, sender=request.user, content=content)
        
        is_winner = False
        xp_earned = 0
        
        if active_battle and active_battle.battle_answer:
            ans = active_battle.battle_answer.lower()
            if ans in content.lower():
                active_battle.battle_answered = True
                active_battle.battle_winner = request.user
                active_battle.save()
                
                xp_profile, _ = StudentXP.objects.get_or_create(student=student)
                xp_profile.add_xp(20) 
                is_winner = True
                xp_earned = 20
                
                StudyGroupMessage.objects.create(
                    room=room,
                    is_aura=True,
                    content=f"⚡ Correct! **{request.user.get_full_name()}** wins the battle and earns +20 XP. The answer was: {ans.title()}."
                )
                return JsonResponse({'status': 'success', 'xp_earned': xp_earned, 'is_winner': True})
                
        if "@aura battle" in content.lower() and not active_battle:
            import openai
            from django.conf import settings
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            prompt = f"Generate a short multiple-choice or short-answer educational trivia question for a {student.current_class.name} class. Return ONLY a JSON object with 'question' and 'answer'. Example: {{\\"question\\": \\"What is 5x5?\\", \\"answer\\": \\"25\\"}}"
            try:
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={ "type": "json_object" }
                )
                q_data = json.loads(res.choices[0].message.content)
                StudyGroupMessage.objects.create(
                    room=room,
                    is_aura=True,
                    is_battle_question=True,
                    battle_answer=q_data.get('answer', ''),
                    content=f"🔴 **AURA BATTLE!** First to answer gets 20 XP!\\n\\n**Question:** {q_data.get('question', '')}"
                )
            except Exception as e:
                pass
        elif "@aura" in content.lower() and not is_winner:
            import openai
            from django.conf import settings
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            try:
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are Aura-T, short insightful responses for students in a group chat. Keep it fun and less than 3 sentences."},
                        {"role": "user", "content": content.replace("@aura", "").replace("@Aura", "").strip()}
                    ],
                )
                StudyGroupMessage.objects.create(
                    room=room,
                    is_aura=True,
                    content=res.choices[0].message.content
                )
            except Exception:
                pass
                
        return JsonResponse({'status': 'success', 'xp_earned': xp_earned, 'is_winner': is_winner})
''')
