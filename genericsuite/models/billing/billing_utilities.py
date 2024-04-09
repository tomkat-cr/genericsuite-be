"""
Billing utilities module
"""
from genericsuite.config.config import Config
from genericsuite.util.app_context import AppContext

DEFAULT_PLAN = "free"
DEBUG = False


class BillingUtilities:
    """
    Billing utilities class
    """
    def __init__(self, app_context: AppContext) -> None:
        self.app_context = app_context
        self.settings = Config(app_context)
        self.user_plan = self.get_user_plan()

    def get_user_plan(self) -> str:
        """
        Get user's current billing plan
        """
        user_plan = self.app_context.get_user_data().get("plan", DEFAULT_PLAN)
        if str(user_plan).strip().lower() not in ["free", "basic", "premium"]:
            user_plan = DEFAULT_PLAN
        return user_plan

    def check_plan(self, plan_type: str) -> bool:
        """
        Returns True if the current user plan is equal to supplied plan
        """
        return self.user_plan == plan_type

    def is_free_plan(self) -> bool:
        """
        Returns True if the current user has a free plan
        """
        return self.check_plan("free")

    def is_basic_plan(self) -> bool:
        """
        Returns True if the current user has a basic plan
        """
        return self.check_plan("basic")

    def is_premium_plan(self) -> bool:
        """
        Returns True if the current user has a premium plan
        """
        return self.check_plan("premium")
