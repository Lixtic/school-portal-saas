import sys, re

with open('templates/teachers/ai_sessions_list.html', 'r', encoding='utf-8') as f:
    text = f.read()

# I will find the "<div class=\"row\">" immediately following "<!-- Interactive Lesson Canvas -->" and replace the canvas up to the Diff Tool
start_marker = "<!-- Interactive Lesson Canvas -->"
end_marker = "<!-- Differentiation Tool -->"

start_idx = text.find(start_marker)
end_idx = text.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_html = '''<!-- Interactive Lesson Canvas -->
              <div class="glass-card p-4 mb-4">
                  <h5 class="fw-bold mb-3"><i class="fas fa-stream me-2 text-primary"></i>Interactive Lesson Canvas</h5>
                  <p class="text-muted small mb-3">Drag AI-generated modules to build your 45-minute flow.</p>

                  <div class="row">
                      <div class="col-md-4">
                          <div class="p-3 bg-light rounded border" id="blocks-bank" style="min-height: 300px;">
                              <h6 class="fw-bold small text-muted text-uppercase mb-2">Smart Blocks Bank</h6>
                              <div class="time-block border-warning border-start-4 shadow-sm" draggable="true">
                                  <div><i class="fas fa-lightbulb text-warning me-2"></i> Hook (Local Story)</div>
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
                          <div class="timeline-canvas h-100 d-flex flex-column text-muted p-2" id="lesson-canvas" style="min-height: 300px; border: 2px dashed #dee2e6; border-radius: 12px; transition: all 0.3s; background: rgba(255,255,255,0.5);">
                              <div class="empty-state d-flex flex-column align-items-center justify-content-center h-100 w-100 py-5">
                                  <i class="fas fa-grip-lines fa-2x mb-2 text-gray-300"></i>
                                  <p>Drag blocks here to sequence lesson</p>
                              </div>
                          </div>
                      </div>
                  </div>
                  
                  <div class="d-flex align-items-center mt-3 w-100 bg-light p-2 rounded border">
                      <span class="small me-2"><i class="fas fa-sliders-h text-primary me-1"></i> Pacing Tool:</span>
                      <input type="range" class="form-range flex-grow-1 mx-2" min="1" max="3" id="diffSlider" value="2">
                      <span class="small ms-2 fw-bold" id="diffLabel" style="width: 120px;">Balanced</span>
                  </div>
              </div>

              '''
    text = text[:start_idx] + new_html + text[end_idx:]
    with open('templates/teachers/ai_sessions_list.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Lesson Canvas updated.")
else:
    print("Could not find start or end markers.")
