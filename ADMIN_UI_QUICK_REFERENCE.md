# 🎨 Modern Admin Dashboard - Quick Reference Guide

## For Developers: How to Use the Admin UI System

### 1. Creating a New Admin Page

Copy this template structure:

```django
{% extends 'admin/admin_base.html' %}
{% load static %}

{% block title %}Page Title Here{% endblock %}

{% block admin_content %}
<link rel="stylesheet" href="{% static 'css/your-page-specific.css' %}">

<div class="glass-bg"></div>

<div class="admin-content-wrapper">
    <!-- Your page content here -->
</div>

{% endblock admin_content %}
```

### 2. Common UI Components

#### Glass Card (Container)
```html
<div class="glass-card p-4 mb-4">
    <h3 class="section-title">Section Title</h3>
    <!-- Content -->
</div>
```

#### Stats Card
```html
<div class="glass-card analytics-tile p-4">
    <div class="d-flex align-items-start justify-content-between mb-3">
        <div class="flex-grow-1">
            <p class="text-muted mb-2 text-uppercase">Label</p>
            <h2 class="metric-value">999</h2>
        </div>
        <div class="metric-icon-wrapper">
            <i class="bi bi-icon-name"></i>
        </div>
    </div>
</div>
```

#### Glass Button
```html
<a class="glass-btn" href="#url">
    <i class="bi bi-icon-name me-2"></i>Button Text
</a>

<!-- Primary variant -->
<a class="glass-btn glass-btn-primary" href="#url">
    <i class="bi bi-icon-name me-2"></i>Primary Button
</a>
```

#### Section Header with Icon
```html
<div class="section-header">
    <div class="section-icon">
        <i class="bi bi-icon-name"></i>
    </div>
    <div>
        <h3 class="section-title">Title</h3>
        <small class="text-muted">Subtitle</small>
    </div>
</div>
```

#### Glass Table
```html
<table class="table glass-table align-middle">
    <thead>
        <tr>
            <th>Column 1</th>
            <th>Column 2</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Data 1</td>
            <td>Data 2</td>
        </tr>
    </tbody>
</table>
```

### 3. Color Utilities

#### Status Colors
```html
<!-- Success -->
<span class="text-success">Success text</span>
<i class="bi bi-icon text-success"></i>

<!-- Warning -->
<span class="text-warning">Warning text</span>
<i class="bi bi-icon text-warning"></i>

<!-- Danger -->
<span class="text-danger">Danger text</span>
<i class="bi bi-icon text-danger"></i>

<!-- Primary -->
<span class="text-primary">Primary text</span>
<i class="bi bi-icon text-primary"></i>
```

#### Gradient Text
```html
<span class="text-gradient">Gradient Text Effect</span>
```

### 4. Layout Patterns

#### Two Column Layout
```html
<div class="row g-3">
    <div class="col-lg-8">
        <!-- 70% width content -->
        <div class="glass-card p-4 h-100">
            <!-- Main content -->
        </div>
    </div>
    <div class="col-lg-4">
        <!-- 30% width sidebar -->
        <div class="glass-card p-4 h-100">
            <!-- Sidebar content -->
        </div>
    </div>
</div>
```

#### Three Column Stats Grid
```html
<div class="row g-3">
    <div class="col-md-6 col-lg-4">
        <!-- Stat card -->
    </div>
    <div class="col-md-6 col-lg-4">
        <!-- Stat card -->
    </div>
    <div class="col-md-6 col-lg-4">
        <!-- Stat card -->
    </div>
</div>
```

#### Four Column Metrics
```html
<div class="row g-3">
    <div class="col-md-6 col-xl-3">
        <!-- Metric tile -->
    </div>
    <!-- Repeat 3 more times -->
</div>
```

### 5. Responsive Utilities

#### Show/Hide on Breakpoints
```html
<!-- Hide on mobile, show on tablet+ -->
<div class="d-none d-md-block">Desktop only</div>

<!-- Show on mobile, hide on tablet+ -->
<div class="d-md-none">Mobile only</div>

<!-- Hidden extra small, inline-flex on medium+ -->
<a class="d-none d-md-inline-flex">Desktop button</a>

<!-- Show on small screens (md breakpoint) -->
<small class="d-none d-sm-inline">Tablet and up</small>
<small class="d-sm-none">Mobile only</small>
```

#### Responsive Spacing
```html
<!-- Margin bottom on all, none on medium+ -->
<div class="mb-4 mb-md-0">Content</div>

<!-- Responsive padding -->
<div class="p-3 p-md-4">Content</div>

<!-- Responsive gap in grid -->
<div class="row g-2 g-md-3">
    <div class="col">Item</div>
</div>
```

### 6. Icon Usage

Bootstrap Icons are available:
```html
<!-- Building icon -->
<i class="bi bi-building"></i>

<!-- Chart icon -->
<i class="bi bi-graph-up-arrow"></i>

<!-- Check icon -->
<i class="bi bi-check-circle"></i>

<!-- Etc... (See https://icons.getbootstrap.com/) -->

<!-- Sizing -->
<i class="bi bi-icon fs-1"></i> <!-- Extra large -->
<i class="bi bi-icon fs-2"></i> <!-- Large -->
<i class="bi bi-icon"></i>      <!-- Normal -->
<i class="bi bi-icon fs-4"></i> <!-- Small -->
```

### 7. Custom CSS (When Needed)

```css
/* admin-your-page.css */

:root {
    --primary-gradient: linear-gradient(135deg, #8b5cf6, #6366f1);
    --card-spacing: 1.5rem;
}

[data-bs-theme="dark"] {
    --primary-gradient: linear-gradient(135deg, #a78bfa, #818cf8);
}

.your-custom-class {
    background: var(--primary-gradient);
    padding: var(--card-spacing);
    border-radius: 10px;
}
```

### 8. Dark Mode Support

Everything automatically supports dark mode via Bootstrap's `data-bs-theme="dark"` attribute.

CSS custom properties automatically adjust colors:
```css
/* Light mode */
--card-bg: #ffffff;
--text-primary: #1a1a1a;

/* Dark mode (automatic) */
[data-bs-theme="dark"] {
    --card-bg: #1e293b;
    --text-primary: #f1f5f9;
}
```

### 9. Form Styling

```html
<form method="post">
    {% csrf_token %}
    
    <div class="mb-3">
        <label for="field" class="form-label">Label</label>
        <input type="text" class="form-control" id="field" name="field">
    </div>
    
    <div class="mb-3">
        <label for="select" class="form-label">Select</label>
        <select class="form-select" id="select" name="select">
            <option>Option 1</option>
        </select>
    </div>
    
    <button type="submit" class="glass-btn glass-btn-primary">
        Submit
    </button>
</form>
```

### 10. Status Indicators

```html
<!-- Status indicator dot -->
<span class="status-indicator bg-success"></span> Success
<span class="status-indicator bg-warning"></span> Warning
<span class="status-indicator bg-danger"></span> Error
<span class="status-indicator bg-primary"></span> Info

<!-- Badges -->
<span class="badge rounded-pill bg-success">Active</span>
<span class="badge rounded-pill bg-warning text-dark">Pending</span>
<span class="badge rounded-pill bg-danger">Inactive</span>
```

## CSS File Structure

```
static/css/
│
├── admin-variables.css
│   └── Global CSS custom properties and color schemes
│
├── admin-components.css
│   ├── Glass-morphism components
│   ├── Navbar and sidebar
│   ├── Card containers
│   └── Button variants
│
├── admin-utilities.css
│   ├── Text utilities
│   ├── Spacing utilities
│   └── Display utilities
│
├── admin-landlord-dashboard.css
│   ├── Dashboard-specific layouts
│   ├── Metric tiles
│   └── Chart containers
│
├── admin-mobile-optimization.css
│   ├── Mobile breakpoint styles
│   ├── Touch-friendly components
│   └── Responsive adjustments
│
└── admin-mobile-utilities.css
    └── Mobile-specific utility classes
```

## Performance Tips

1. **Use `<link rel="preload">` for critical CSS**
   ```html
   <link rel="preload" as="style" href="{% static 'css/admin-variables.css' %}">
   ```

2. **Minimize custom CSS per page**
   - Reuse existing classes
   - Use CSS custom properties
   - Avoid duplicate styles

3. **Lazy load non-critical content**
   ```html
   <!-- Charts, tables with many rows, etc -->
   <div class="lazy-load" data-url="{% url 'api:chart' %}"></div>
   ```

4. **Use CDN for Bootstrap Icons**
   - Already included in `admin_base.html`
   - No additional requests needed

## Troubleshooting

### "Glass effect not showing"
- Check if `.glass-card` class is applied
- Ensure `admin-components.css` is loaded
- Verify dark mode theme setting

### "Colors look different in dark mode"
- Add dark mode styles using `[data-bs-theme="dark"]`
- Use CSS custom properties instead of hard-coded colors
- Test in both light and dark themes

### "Mobile layout broken"
- Check responsive classes (`.d-none`, `.d-md-block`)
- Verify Bootstrap grid columns sum <= 12
- Test with viewport width < 768px

### "Sidebar not appearing"
- Only visible on pages extending `admin_base.html`
- Not included on public pages (signup, login, etc.)
- Must use `{% extends 'admin/admin_base.html' %}`

## Examples

### Example: Analytics Dashboard
```django
{% extends 'admin/admin_base.html' %}
{% load static %}

{% block title %}Analytics{% endblock %}

{% block admin_content %}
<div class="glass-bg"></div>

<!-- Header -->
<div class="glass-card p-4 mb-4">
    <div class="d-flex justify-content-between align-items-center">
        <h1 class="section-title mb-0">Analytics Dashboard</h1>
        <a class="glass-btn" href="#export">Export</a>
    </div>
</div>

<!-- Metrics -->
<div class="row g-3 mb-4">
    {% for metric in metrics %}
    <div class="col-md-6 col-lg-3">
        <div class="glass-card analytics-tile p-4">
            <div class="d-flex align-items-start justify-content-between">
                <div>
                    <p class="text-muted mb-2 text-uppercase">{{ metric.label }}</p>
                    <h2 class="metric-value">{{ metric.value }}</h2>
                </div>
                <div class="metric-icon-wrapper">
                    <i class="bi {{ metric.icon }}"></i>
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>

<!-- Chart -->
<div class="glass-card p-4">
    <div class="section-header mb-4">
        <div class="section-icon">
            <i class="bi bi-bar-chart"></i>
        </div>
        <h3 class="section-title mb-0">Trend</h3>
    </div>
    <canvas id="chart"></canvas>
</div>

{% endblock %}
```

---

**Remember**: Keep designs consistent, use existing classes, and test on mobile!
