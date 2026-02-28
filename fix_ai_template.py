import sys, re
with open('templates/teachers/ai_sessions_list.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace hardcoded map grid
old_grid = '''<div class="heatmap-grid pb-2">
                    <!-- Generating mock students for visual effect -->
                    <div class="student-tile tile-good" title="Kwame - On target">
                        <span class="fw-bold">Kwame</span>
                        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e4/Sparkline_example.png" class="sparkline" style="filter: grayscale(1) opacity(0.5);">
                    </div>
                    <div class="student-tile tile-excellent" title="Efia - Excelling">
                        <span class="fw-bold">Efia</span>
                        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e4/Sparkline_example.png" class="sparkline" style="filter: grayscale(1) opacity(0.5);">
                    </div>
                    <div class="student-tile tile-struggling" data-bs-toggle="popover" data-bs-trigger="hover" title="Kofi's Status" data-bs-content="Struggling with 'Factoring'. Used 'Hint' 4 times. Click to open chat.">
                        <span class="fw-bold">Kofi </span>
                        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e4/Sparkline_example.png" class="sparkline" style="filter: grayscale(1) opacity(0.5);">
                    </div>
                    <div class="student-tile tile-good" title="Yaw - Progressing"><span class="fw-bold">Yaw</span></div>
                    <div class="student-tile tile-good" title="Adjoa - Progressing"><span class="fw-bold">Adjoa</span></div>
                    <div class="student-tile tile-excellent" title="Zainab - Excelling"><span class="fw-bold">Zainab</span></div>
                    <div class="student-tile tile-struggling" title="Ama - Needs Help"><span class="fw-bold">Ama </span></div>
                    <div class="student-tile tile-good" title="Kweku - Progressing"><span class="fw-bold">Kweku</span></div>
                    <div class="student-tile tile-excellent" title="Abena - Excelling"><span class="fw-bold">Abena</span></div>
                    <div class="student-tile tile-good" title="Esi - Progressing"><span class="fw-bold">Esi</span></div>
                    <div class="student-tile tile-struggling" title="Kwesi - Needs Help"><span class="fw-bold">Kwesi </span></div>
                    <div class="student-tile tile-good" title="Akosua - Progressing"><span class="fw-bold">Akosua</span></div>
                </div>'''

new_grid = '''<div class="heatmap-grid pb-2">
                    {% for student in student_data %}
                        {% if student.status == 'excellent' %}
                            <div class="student-tile tile-excellent" title="{{ student.name }} - Excelling" data-bs-toggle="popover" data-bs-trigger="hover" data-bs-content="{{ student.tooltip }}">
                                <span class="fw-bold">{{ student.name }}</span>
                                <img src="https://upload.wikimedia.org/wikipedia/commons/e/e4/Sparkline_example.png" class="sparkline" style="filter: grayscale(1) opacity(0.5);">
                            </div>
                        {% elif student.status == 'struggling' %}
                            <div class="student-tile tile-struggling" data-bs-toggle="popover" data-bs-trigger="hover" title="{{ student.name }}'s Status" data-bs-content="{{ student.tooltip }}">
                                <span class="fw-bold">{{ student.name }} </span>
                                <img src="https://upload.wikimedia.org/wikipedia/commons/e/e4/Sparkline_example.png" class="sparkline" style="filter: grayscale(1) opacity(0.5);">
                            </div>
                        {% else %}
                            <div class="student-tile tile-good" title="{{ student.name }} - Progressing" data-bs-toggle="popover" data-bs-trigger="hover" data-bs-content="{{ student.tooltip }}">
                                <span class="fw-bold">{{ student.name }}</span>
                            </div>
                        {% endif %}
                    {% empty %}
                        <p class="text-muted small">No student data available. Ensure your class assignments are configured.</p>
                    {% endfor %}
                </div>'''

text = text.replace(old_grid, new_grid)

# Replace hardcoded parent updates
old_parents = '''<div class="list-group">
                        <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1 fw-bold">Mr. Osei (Ama's Father)</h6>
                                <p class="mb-0 small text-muted">"Hi Mr. Osei, Ama did great with 'Friction' today, but she's still a bit confused about 'Mass.' Here is a video link..."</p>
                            </div>
                            <button class="btn btn-sm btn-success rounded-pill px-3">Send <i class="fas fa-paper-plane ms-1"></i></button>
                        </div>
                        <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1 fw-bold">Mrs. Mensah (Kofi's Mother)</h6>
                                <p class="mb-0 small text-muted">"Hi Mrs. Mensah, Kofi is struggling with 'Negative Coefficients'. I have assigned him to a remedial group tomorrow..."</p>
                            </div>
                            <button class="btn btn-sm btn-success rounded-pill px-3">Send <i class="fas fa-paper-plane ms-1"></i></button>
                        </div>
                    </div>'''

new_parents = '''<div class="list-group">
                        {% for update in parent_updates %}
                        <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1 fw-bold">{{ update.parent_name }} ({{ update.student_name }}'s Parent)</h6>
                                <p class="mb-0 small text-muted">"{{ update.draft }}"</p>
                            </div>
                            <button class="btn btn-sm btn-success rounded-pill px-3" onclick="alert('Message sent to {{ update.parent_name }}!')">Send <i class="fas fa-paper-plane ms-1"></i></button>
                        </div>
                        {% empty %}
                        <div class="text-muted small p-2">No parent updates available to draft.</div>
                        {% endfor %}
                    </div>'''

text = text.replace(old_parents, new_parents)

# Replace Basic 8 Science with variable
text = text.replace('<span class="badge bg-secondary">Basic 8 Science</span>', '<span class="badge bg-secondary">{{ class_name_display }}</span>')

# Replace aura co-pilot hardcodes
text = text.replace('<p class="mb-1 small"><strong>Kofi, Ama, and Yaw</strong> are stuck on \'Factoring Quadratics\'.</p>', '<p class="mb-1 small"><strong>{{ struggling_count }} students</strong> are struggling with recent materials.</p>')
text = text.replace('<p class="mb-1 small"><strong>85%</strong> scored above target on yesterday\'s Knowledge Check.</p>', '<p class="mb-1 small"><strong>{{ excelling_count }} students</strong> are excelling in their metrics.</p>')

with open('templates/teachers/ai_sessions_list.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated Template")
