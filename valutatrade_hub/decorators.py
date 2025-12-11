#!/usr/bin/env python3
"""Декораторы для логирования операций."""

import functools

from .logging_config import get_logger

logger = get_logger()


def log_action(action_name: str, verbose: bool = False):
    """Декоратор для логирования операций (buy/sell/register/login)."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            username = "unknown"
            try:
                if "username" in kwargs:
                    username = kwargs["username"]
                elif args and len(args) > 0:
                    if action_name in ["register", "login"] and len(args) > 0:
                        username = args[0]
                    elif action_name in ["buy", "sell"]:
                        from core.usecases import get_logged_user
                        user = get_logged_user()
                        if user:
                            username = user.username
            except Exception:
                username = "unknown"

            extra_info = ""
            if action_name in ["buy", "sell"] and "currency" in kwargs:
                currency = kwargs["currency"]
                amount = kwargs.get("amount", 0)
                extra_info = f" currency='{currency}' amount={amount}"

            try:
                result = func(*args, **kwargs)
                logger.info(
                    f"ACTION {action_name.upper()} user='{username}'"
                    f"{extra_info} result=OK"
                )
                return result
            except Exception as e:
                logger.error(
                    f"ACTION {action_name.upper()} user='{username}'"
                    f"{extra_info} result=ERROR type={type(e).__name__} "
                    f"message={str(e)}"
                )
                raise

        return wrapper

    return decorator
