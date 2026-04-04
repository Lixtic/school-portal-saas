"""Credit utilities for individual portal users (mirrors teachers/addon_utils.py credit functions)."""
from django.db import transaction


# ── Credit costs per AI action ──────────────────────────────────
CREDIT_COSTS = {
    'lesson_gen':     1,
    'exercise_gen':   1,
    'assignment_gen': 1,
    'study_guide':    2,
    'slide_gen':      3,
    'bulk_gen':       5,
    'report_card':    2,
    'question_gen':   2,
    'differentiate':  2,
    'other':          1,
}

WELCOME_BONUS_CREDITS = 10


def _get_or_create_balance(user):
    """Return the IndividualCreditBalance for *user*, creating with welcome bonus if new."""
    from individual_users.models import IndividualCreditBalance, IndividualCreditTransaction
    bal, created = IndividualCreditBalance.objects.get_or_create(
        user=user,
        defaults={'balance': WELCOME_BONUS_CREDITS, 'total_purchased': 0, 'total_used': 0},
    )
    if created:
        IndividualCreditTransaction.objects.create(
            user=user,
            amount=WELCOME_BONUS_CREDITS,
            balance_after=WELCOME_BONUS_CREDITS,
            transaction_type='bonus',
            description=f'Welcome bonus — {WELCOME_BONUS_CREDITS} free AI credits',
        )
    return bal


def get_credit_balance(user):
    """Return the current credit balance for *user*."""
    if not user.is_authenticated:
        return 0
    bal = _get_or_create_balance(user)
    return bal.balance


def deduct_credits(user, action_type, description=''):
    """Deduct credits for an AI action. Returns (success, error_dict_or_None)."""
    from individual_users.models import IndividualCreditBalance, IndividualCreditTransaction
    cost = CREDIT_COSTS.get(action_type, 1)

    with transaction.atomic():
        bal = IndividualCreditBalance.objects.select_for_update().get(user=user)
        if bal.balance < cost:
            return False, {
                'status': 'error',
                'error_code': 'insufficient_credits',
                'message': (
                    f'You need {cost} credit{"s" if cost != 1 else ""} for this action '
                    f'but only have {bal.balance}. Buy more credits from the Add-on Store.'
                ),
                'balance': bal.balance,
                'cost': cost,
            }
        bal.balance -= cost
        bal.total_used += cost
        bal.save(update_fields=['balance', 'total_used', 'updated_at'])

        action_label = action_type.replace('_', ' ').title()
        IndividualCreditTransaction.objects.create(
            user=user,
            amount=-cost,
            balance_after=bal.balance,
            transaction_type='usage',
            description=description or f'{action_label} (-{cost} credit{"s" if cost != 1 else ""})',
        )
    return True, None


def add_credits(user, amount, transaction_type='purchase', description='', payment_reference=''):
    """Add credits to a user's balance. Returns the updated balance object."""
    from individual_users.models import IndividualCreditBalance, IndividualCreditTransaction

    with transaction.atomic():
        _get_or_create_balance(user)
        bal = IndividualCreditBalance.objects.select_for_update().get(user=user)
        bal.balance += amount
        if transaction_type == 'purchase':
            bal.total_purchased += amount
        bal.save(update_fields=['balance', 'total_purchased', 'updated_at'])

        IndividualCreditTransaction.objects.create(
            user=user,
            amount=amount,
            balance_after=bal.balance,
            transaction_type=transaction_type,
            description=description,
            payment_reference=payment_reference,
        )
    return bal
