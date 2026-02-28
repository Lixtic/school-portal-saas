#!/usr/bin/env python3
"""Replace the Aura panel with a dynamic version."""

with open('templates/base.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find start and end lines of the Aura panel
start_line = None

for i, line in enumerate(lines):
    if '<div id="aura-copilot-container">' in line:
        start_line = i
        break

if start_line is None:
    print('Container not found')
    exit(1)

print(f'Container starts at line {start_line + 1}')

# Count div depth to find end
depth = 0
end_line = None
for i in range(start_line, len(lines)):
    depth += lines[i].count('<div')
    depth -= lines[i].count('</div>')
    if depth == 0 and i > start_line:
        end_line = i
        break

print(f'Container ends at line {end_line + 1}')

# New Aura panel HTML
new_panel_lines = '''<div id="aura-copilot-container">
    <div id="auraPanel" class="aura-panel">
        <div class="aura-header d-flex justify-content-between align-items-center">
            <div>
                <h6 class="mb-0 fw-bold"><i class="fas fa-brain me-2"></i>Aura-T</h6>
                <small class="opacity-75">{% if aura_teacher_classes %}{{ aura_teacher_classes|join:", " }}{% else %}Your Classes{% endif %}</small>
            </div>
            <button class="btn-close btn-close-white" onclick="document.getElementById('auraPanel').classList.remove('show');"></button>
        </div>
        <div class="aura-body" id="auraBody">
            <h6 class="text-uppercase text-muted small fw-bold mb-3">
                <i class="fas fa-chalkboard-teacher me-1"></i> 
                {% if aura_teacher_subjects %}Teaching: {{ aura_teacher_subjects|join:", " }}{% else %}Your Subjects{% endif %}
            </h6>

            {% if aura_class_summary %}
            <div class="aura-insight-card" {% if aura_class_summary.struggling_count > 0 %}style="border-left-color: #ffc107;"{% else %}style="border-left-color: #28a745;"{% endif %}>
                <div class="d-flex align-items-center mb-2">
                    {% if aura_class_summary.struggling_count > 0 %}
                    <span class="badge bg-warning text-dark me-2">Alert</span>
                    <span class="small fw-bold">Students Need Help</span>
                    {% else %}
                    <span class="badge bg-success me-2">All Good</span>
                    <span class="small fw-bold">Class On Track</span>
                    {% endif %}
                </div>
                <p class="small mb-2">
                    {{ aura_class_summary.total_students }} students total{% if aura_class_summary.struggling_count > 0 %}, {{ aura_class_summary.struggling_count }} struggling{% endif %}
                </p>
                {% if aura_struggling_students %}
                <div class="small text-muted mb-2">
                    {% for s in aura_struggling_students %}<span class="badge bg-danger me-1">{{ s.name }}: {{ s.avg_score }}%</span>{% endfor %}
                </div>
                {% endif %}
            </div>
            {% else %}
            <div class="aura-insight-card">
                <p class="small mb-2 text-muted">No class data available yet.</p>
            </div>
            {% endif %}

            <div class="aura-insight-card" style="border-left-color: #667eea;">
                <a href="{% url 'teachers:ai_sessions_list' %}" class="btn btn-sm btn-outline-primary w-100" style="font-size: 0.75rem;"><i class="fas fa-rocket me-1"></i> Open Command Centre</a>
            </div>

            <!-- Aura Chat Messages -->
            <div id="auraChatMessages" class="mt-3" style="max-height: 200px; overflow-y: auto;"></div>
        </div>
        <!-- Chat Input -->
        <div class="border-top p-2">
            <form id="auraChatForm" class="d-flex gap-2" data-no-loader>
                <input type="text" id="auraChatInput" class="form-control form-control-sm" placeholder="Ask Aura about your classes..." autocomplete="off" required style="font-size: 0.8rem;">
                <button type="submit" class="btn btn-sm btn-primary"><i class="fas fa-paper-plane"></i></button>
            </form>
        </div>
        <div class="bg-light p-2 text-center border-top">
            <small class="text-muted"><i class="fas fa-bolt text-warning me-1"></i> Powered by Aura-T</small>
        </div>
    </div>
    <div class="aura-orb-btn pulse-amber" onclick="document.getElementById('auraPanel').classList.toggle('show');" title="Open Aura Co-Pilot">
        <i class="fas fa-robot"></i>
    </div>
</div>

<!-- Aura-T Chat Script -->
<script>
(function() {
    const form = document.getElementById('auraChatForm');
    const input = document.getElementById('auraChatInput');
    const messagesContainer = document.getElementById('auraChatMessages');
    if (!form || !input || !messagesContainer) return;

    let isProcessing = false;

    const csrftoken = (name => {
        const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return match ? match[2] : '';
    })('csrftoken');

    function appendMessage(text, type) {
        const div = document.createElement('div');
        div.className = 'small p-2 rounded mb-2 ' + (type === 'user' ? 'bg-primary text-white ms-auto' : 'bg-light');
        div.style.maxWidth = '85%';
        div.style.width = 'fit-content';
        if (type === 'user') div.style.marginLeft = 'auto';
        div.textContent = text;
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return div;
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        if (isProcessing) return;

        const question = (input.value || '').trim();
        if (!question) return;

        isProcessing = true;
        input.disabled = true;

        appendMessage(question, 'user');
        input.value = '';

        const loadingDiv = appendMessage('Thinking...', 'bot');

        try {
            const res = await fetch('{% url "academics:copilot_assistant" %}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                },
                body: JSON.stringify({ question: question, role: 'teacher' }),
            });

            loadingDiv.remove();

            if (!res.ok) {
                appendMessage('Sorry, I could not process that.', 'bot');
                isProcessing = false;
                input.disabled = false;
                return;
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '';
            const botDiv = appendMessage('', 'bot');

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                fullText += chunk;
                botDiv.textContent = fullText;
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        } catch (err) {
            loadingDiv.remove();
            appendMessage('Network error. Please try again.', 'bot');
        } finally {
            isProcessing = false;
            input.disabled = false;
            input.focus();
        }
    });
})();
</script>
'''

# Build new file content
new_lines = lines[:start_line] + [new_panel_lines] + lines[end_line + 1:]

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Aura panel replaced successfully!')
