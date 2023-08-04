from pathlib import Path

import git
from git.exc import GitCommandError, InvalidGitRepositoryError
from LittlePaimon.utils import NICKNAME
from nonebot.utils import run_sync

from .logger import Logger


@run_sync
def do_update():
    try:
        repo = git.Repo(Path(__file__).parent.parent.absolute())
    except InvalidGitRepositoryError:
        return "没有发现git仓库，无法通过git更新，请手动下载最新版本的文件进行替换。"
    Logger.info("验证签到插件更新", "开始执行<m>git pull</m>更新操作")
    origin = repo.remotes.origin
    try:
        origin.pull()
        repo_msg = (
            repo.head.commit.message.replace(":bug:", "🐛")
            .replace(":sparkles:", "✨")
            .replace(":memo:", "📝")
            .replace(":art:", "🎨")
        )
        msg = f"签到插件更新完成\n最新更新日志为：\n{repo_msg}\n可使用命令[@bot 重启]重启{NICKNAME}"
    except GitCommandError as e:
        if "timeout" in e.stderr or "unable to access" in e.stderr:
            msg = "签到插件更新失败，连接git仓库超时，请重试或修改源为代理源后再重试。"
        elif "Your local changes" in e.stderr:
            msg = f"签到插件更新失败，本地修改过文件导致冲突，请解决冲突后再更新。\n{e.stderr}"
        else:
            msg = f"签到插件更新失败，错误信息：{e.stderr}，请尝试手动进行更新"
    return msg
