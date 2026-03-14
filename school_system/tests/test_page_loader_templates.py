from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class PageLoaderTemplateRegressionTests(SimpleTestCase):
    def _read_template(self, relative_path: str) -> str:
        file_path = Path(settings.BASE_DIR) / relative_path
        self.assertTrue(file_path.exists(), f"Template not found: {relative_path}")
        return file_path.read_text(encoding="utf-8")

    def test_base_template_contains_global_loader_hooks(self):
        content = self._read_template("templates/base.html")

        # Core global loader DOM hooks and JS API should remain present.
        self.assertIn('id="pageLoader"', content)
        self.assertIn('id="globalLoader"', content)
        self.assertIn('function showLoader(', content)
        self.assertIn('function hideLoader(', content)

        # Skeleton loader contract used by heavy pages.
        self.assertIn('has-skeleton-loader', content)
        self.assertIn('{% block body_class %}', content)
        self.assertIn('is-page-loading', content)

    def test_heavy_pages_opt_into_skeleton_loader(self):
        template_expectations = {
            "templates/dashboard/admin_dashboard.html": "has-skeleton-loader",
            "templates/dashboard/teacher_dashboard.html": "has-skeleton-loader",
            "templates/students/student_list.html": "has-skeleton-loader",
            "templates/teachers/analytics_dashboard.html": "has-skeleton-loader",
            "templates/academics/ai_tutor.html": "has-skeleton-loader",
            "templates/teachers/presentations/list.html": "has-skeleton-loader",
            "templates/teachers/presentations/editor.html": "has-skeleton-loader",
            "templates/teachers/assignment_creator.html": "has-skeleton-loader",
        }

        for template_path, expected_class in template_expectations.items():
            with self.subTest(template=template_path):
                content = self._read_template(template_path)
                self.assertIn("{% block body_class %}", content)
                self.assertIn(expected_class, content)
