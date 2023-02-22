from typing import List
from pydantic import BaseModel, Field
from LittlePaimon.utils.files import load_yaml, save_yaml
from pathlib import Path

PAIMON_CONFIG = Path() / "config" / "Captcha_config.yml"


class ConfigModel(BaseModel):
    auto_myb_enable: bool = Field(True, alias='米游币验证自动获取开关')
    auto_myb_hour: int = Field(8, alias='米游币验证开始执行时间(小时)')
    auto_myb_minute: int = Field(0, alias='米游币验证开始执行时间(分钟)')

    auto_sign_enable: bool = Field(False, alias='米游社验证自动签到开关')
    auto_sign_hour: int = Field(0, alias='米游社验证签到开始时间(小时)')
    auto_sign_minute: int = Field(5, alias='米游社验证签到开始时间(分钟)')

    ssbq_enable: bool = Field(True, alias='实时便签验证检查开关')
    ssbq_begin: int = Field(0, alias='实时便签验证停止检查开始时间')
    ssbq_end: int = Field(6, alias='实时便签验证停止检查结束时间')
    ssbq_check: int = Field(16, alias='实时便签验证检查间隔')

    change_api: bool = Field(True, alias='打码平台')
    third_api: str = Field('', alias='第三方链接')
    rrocr_key: str = Field('', alias='人人打码appkey')
    member_allow_list: List[int] = Field([], alias='开启验证的成员列表')
    group_allow_list: List[int] = Field([], alias='开启验证的群列表')

    @property
    def alias_dict(self):
        return {v.alias: k for k, v in self.__fields__.items()}

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__fields__:
                self.__setattr__(key, value)
            elif key in self.alias_dict:
                self.__setattr__(self.alias_dict[key], value)


class ConfigManager:
    if PAIMON_CONFIG.exists():
        config = ConfigModel.parse_obj(load_yaml(PAIMON_CONFIG))
    else:
        config = ConfigModel()
        save_yaml(config.dict(by_alias=True), PAIMON_CONFIG)

    @classmethod
    def save(cls):
        save_yaml(cls.config.dict(by_alias=True), PAIMON_CONFIG)


config = ConfigManager.config
