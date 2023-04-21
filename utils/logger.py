from typing import Dict

from nonebot import logger as nb_logger
from nonebot.utils import escape_tag


class Logger:
    """
    自定义格式、色彩logger
    """

    @staticmethod
    def info(
        command: str,
        info: str = "",
        param: Dict[str, any] = None,
        result: str = "",
        result_type: bool = True,
    ):
        param_str = (
            " ".join([f"{k}<m>{escape_tag(str(v))}</m>" for k, v in param.items()])
            if param
            else ""
        )
        result_str = (
            f"<g>{escape_tag(result)}</g>"
            if result_type
            else f"<r>{escape_tag(result)}</r>"
            if result
            else ""
        )
        nb_logger.opt(colors=True).info(
            f"<u><y>[{command}]</y></u>{info}{param_str}{result_str}"
        )
