import sys, re

with open('templates/teachers/ai_sessions_list.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_canvas_html = '''<div class="row">
                    <div class="col-md-4">
                        <div class="p-3 bg-light rounded border">
                            <h6 class="fw-bold small text-muted text-uppercase mb-2">Smart Blocks Bank</h6>
                            <div class="time-block border-warning border-start-4 shadow-sm" draggable="true">
                                <div><i class="fas fa-lightbulb text-warning me-2"></i> Hook (Makola Market local story)</div>
                                <span class="badge bg-light text-dark">5m</span>
                            </div>
                            <div class="time-block shadow-sm" draggable="true">
                                <div><i class="fas fa-chalkboard-teacher text-primary me-2"></i> Direct Instruction</div>
                                <span class="badge bg-light text-dark">15m</span>
                            </div>
                            <div class="time-block shadow-sm" draggable="true">
                                <div><i class="fas fa-users text-info me-2"></i> Group Practice</div>
                                <span class="badge bg-light text-dark">15m</span>
                            </div>
                            <div class="time-block border-success shadow-sm" draggable="true">
                                <div><i class="fas fa-check-circle text-success me-2"></i> Exit Ticket</div>
                                <span class="badge bg-light text-dark">10m</span>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-8">
                        <div class="timeline-canvas h-100 d-flex flex-column align-items-center justify-content-center text-muted">
                            <i class="fas fa-grip-lines fa-2x mb-2 text-gray-300"></i>
                            <p>Drag blocks here to sequence lesson</p>
                            <div class="d-flex align-items-center mt-3 w-75">
                                <span class="small me-2">Difficulty/Speed</span>
                                <input type="range" class="form-range flex-grow-1 mx-2" min="1" max="3" id="diffSlider" value="2">
                                <span class="small ms-2" id="diffLabel">Balanced</span>
                            </div>
                        </div>
                    </div>
                </div>'''

new_canvas_html = '''<div class="row">
                    <div class="col-md-4">
                        <div class="p-3 bg-light rounded border" id="blocks-bank">
                            <h6 class="fw-bold small text-muted text-uppercase mb-2">Smart Blocks Bank</h6>
                            <div class="time-block border-warning border-start-4 shadow-sm" draggable="true">
                                <div><i class="fas fa-lightbulb text-warning me-2"></i> Hook (Makola Market local story)</div>
                                <span class="badge bg-light text-dark">5m</span>
                            </div>
                            <div class="time-block shadow-sm" draggable="true">
                                <div><i class="fas fa-chalkboard-teacher text-primary me-2"></i> Direct Instruction</div>
                                <span class="badge bg-light text-dark">15m</span>
                            </div>
                            <div class="time-block shadow-sm" draggable="true">
                                <div><i class="fas fa-users text-info me-2"></i> Group Practice</div>
                                <span class="badge bg-light text-dark">15m</span>
                            </div>
                            <div class="time-block border-success shadow-sm" draggable="true">
                                <div><i class="fas fa-check-circle text-success me-2"></i> Exit Ticket</div>
                                <span class="badge bg-light text-dark">10m</span>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-8">
                        <div class="timeline-canvas h-100 d-flex flex-column text-muted p-2" id="lesson-canvas" style="min-height: 250px;">
                            <div class="empty-state d-flex flex-column align-items-center justify-content-center h-100">
                                <i class="fas fa-grip-lines fa-2x mb-2 text-gray-300"></i>
                                <p>Drag blocks here to sequence lesson</p>
                            </div>
                        </div>
                        <div class="d-flex align-items-center mt-3 w-100 bg-light p-2 rounded border">
                            <span class="small me-2"><i class="fas fa-sliders-h text-primary me-1"></i> Pacing Tool:</span>
                            <input type="range" class="form-range flex-grow-1 mx-2" min="1" max="3" id="diffSlider" value="2">
                            <span class="small ms-2 fw-bold" id="diffLabel">Balanced</span>
                        </div>
                    </div>
                </div>'''

if old_canvas_html in text:
    text = text.replace(old_canvas_html, new_canvas_html)
else:
    print("Could not find the target old_canvas_html in the script.")

# Let's insert the JS at the end of the file
js_code = '''
<style>
.time-block.dragging {
    opacity: 0.5;
    transform: scale(0.95);
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    z-index: 100;
}
.timeline-canvas.drag-over {
    background-color: var(--bs-light);
    border-color: var(--bs-primary) !important;
}
.empty-state { pointer-events: none; }
</style>
<script>
document.addEventListener('DOMContentLoaded', () => {
    // Tooltip init
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Popover(tooltipTriggerEl)
    });

    const draggables = document.querySelectorAll('.time-block');
    const canvases = [document.getElementById('lesson-canvas'), document.getElementById('blocks-bank')];
    const lessonCanvas = document.getElementById('lesson-canvas');

    draggables.forEach(draggable => {
        draggable.addEventListener('dragstart', () => {
            draggable.classList.add('dragging');
        });

        draggable.addEventListener('dragend', () => {
            draggable.classList.remove('dragging');
            checkCanvasState();
        });
    });

    canvases.forEach(canvas => {
        if(!canvas) return;
        
        canvas.addEventListener('dragover', e => {
            e.preventDefault();
            if (canvas.id === 'lesson-canvas') {
                canvas.classList.add('drag-over');
            }
            
            const afterElement = getDragAfterElement(canvas, e.clientY);
            const draggable = document.querySelector('.dragging');
            if (draggable) {
                if (afterElement == null) {
                    canvas.appendChild(draggable);
                } else {
                    canvas.insertBefore(draggable, afterElement);
                }
            }
        });
        
        canvas.addEventListener('dragleave', e => {
            if (canvas.id === 'lesson-canvas') {
                canvas.classList.remove('drag-over');
            }
        });

        canvas.addEventListener('drop', e => {
            if (canvas.id === 'lesson-canvas') {
                canvas.classList.remove('drag-over');
                // Could emit haptic feedback or simple sound here
            }
        });
    });

    function checkCanvasState() {
        if(!lessonCanvas) return;
        const blocks = lessonCanvas.querySelectorAll('.time-block');
        const emptyState = lessonCanvas.querySelector('.empty-state');
        
        if (blocks.length > 0) {
            if(emptyState) emptyState.style.display = 'none';
        } else {
            if(emptyState) emptyState.style.display = 'flex';
        }
    }

    function getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.time-block:not(.dragging)')];
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    // Difficulty slider logic
    const diffSlider = document.getElementById('diffSlider');
    const diffLabel = document.getElementById('diffLabel');
    if(diffSlider && diffLabel) {
        diffSlider.addEventListener('input', function() {
            if(this.value == 1) { diffLabel.innerText = "Remedial (Slower)"; diffLabel.className = 'small ms-2 fw-bold text-warning'; }
            else if(this.value == 2) { diffLabel.innerText = "Balanced"; diffLabel.className = 'small ms-2 fw-bold text-dark'; }
            else { diffLabel.innerText = "Accelerated (Fast)"; diffLabel.className = 'small ms-2 fw-bold text-success'; }
        });
    }
});
</script>
{% endblock %}
'''

if "const draggables = document.querySelectorAll('.time-block');" not in text:
    text = text.replace('{% endblock %}', js_code)

with open('templates/teachers/ai_sessions_list.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Applied interactive drag and drop to lesson canvas.")
