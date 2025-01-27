from enum import StrEnum
from typing import Optional


class Stage(StrEnum):
    LOCAL = 'local'
    DEV = 'dev'
    UAT = 'uat'
    PROD = 'prod'


def get_stage_from_env(env_var: str) -> Stage:
    """
    Checks if the environment variable matches any value in the Stage enum.
    :param env_var: The environment variable value as a string.
    :return: The corresponding Stage enum value or None if invalid.
    """
    try:
        return Stage(env_var)
    except ValueError:
        raise ValueError(f"Invalid STAGE environment variable: {env_var}")