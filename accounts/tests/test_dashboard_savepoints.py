from django.test import TestCase, RequestFactory
from django.db import OperationalError, transaction, connection
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth import get_user_model

from accounts.views import dashboard
from teachers.models import Teacher


class DashboardSavepointTest(TestCase):
    """Ensure dashboard view recovers when introspection/query fails.

    The dashboard performs schema introspection and several DB queries.
    If an early DB error aborts the transaction, later queries will raise
    "current transaction is aborted". The saved-point-based fixes in
    `accounts.views` should isolate failures so the view still renders.
    """

    def setUp(self):
        self.factory = RequestFactory()
        User = get_user_model()
        # Create a minimal teacher user and profile
        self.user = User.objects.create_user(
            username='t1', email='t1@example.com', password='pass', user_type='teacher', first_name='T', last_name='One'
        )
        Teacher.objects.create(
            user=self.user,
            employee_id='EID1',
            date_of_birth='1990-01-01',
            date_of_joining='2010-01-01',
            qualification='BEd'
        )

    def _add_session(self, request):
        mw = SessionMiddleware()
        mw.process_request(request)
        request.session.save()

    def test_dashboard_handles_introspection_error(self):
        req = self.factory.get('/GirlsModel/dashboard/')
        req.user = self.user
        # Provide a dummy tenant so the view treats this as a tenant dashboard
        req.tenant = type('T', (), {'schema_name': 'school1'})()
        self._add_session(req)

        # Monkeypatch introspection to raise OperationalError
        original = connection.introspection.get_table_description

        def fake_get_table_description(cursor, table_name):
            raise OperationalError('simulated introspection failure')

        connection.introspection.get_table_description = fake_get_table_description

        try:
            # Run the view inside an outer transaction to simulate ATOMIC_REQUESTS
            with transaction.atomic():
                response = dashboard(req)
                # View should render a dashboard page (status 200) instead of erroring
                self.assertEqual(response.status_code, 200)
        finally:
            connection.introspection.get_table_description = original
