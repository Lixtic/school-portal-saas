"""Context processor to inject credit balance into all individual portal templates."""


def individual_credits(request):
    """Return credit balance for authenticated individual-portal users."""
    if not request.user.is_authenticated:
        return {}

    # Only run for individual portal requests (avoid overhead on tenant pages)
    if not getattr(request, 'resolver_match', None):
        return {}
    namespace = getattr(request.resolver_match, 'namespace', '')
    if namespace != 'individual':
        return {}

    from individual_users.credit_utils import get_credit_balance

    balance = get_credit_balance(request.user)
    return {
        'iu_credit_balance': balance,
        'iu_credits_low': balance <= 3,
    }
