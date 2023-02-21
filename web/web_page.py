from amis import Form, LevelEnum, InputText, Divider, InputText, Alert, Html, InputTime
from amis import PageSchema, Page, Switch, Remark, InputTag, Action

from LittlePaimon.web.pages import admin_app

action_button = [
    Action(label="保存", level=LevelEnum.success, type="submit"),
    Action(label="重置", level=LevelEnum.warning, type="reset"),
]
coding_form = Form(
    title="过验证码配置",
    name='abyss_config',
    api='post:/LittlePaimon/api/abyss_config',
    body=[
        Switch(
            label="打码平台选择",
            name="打码平台",
            value="${打码平台}",
            labelRemark=Remark(
                shape="circle", content="选择打码平台,如果选择三方并且填写了人人key，会在失败后尝试使用人人继续"
            ),
            onText="人人",
            offText="三方",
        ),
        InputText(
            label="第三方请求链接",
            name="第三方链接",
            value="${第三方链接}",
            placeholder="输入第三方平台的打码请求链接(需包含token值)",
            labelRemark=Remark(
                shape="circle",
                content="例如：http(s)://abc.bb?token=xxx&,或者http("
                "s)://abc.bb/token=xxx$，具体请看第三方平台api",
            ),
        ),
        InputText(
            label="人人appkey",
            name="人人打码appkey",
            value="${人人打码appkey}",
            placeholder="输入你在人人打码获取的appkey",
            labelRemark=Remark(
                shape="circle", content="用于签到，米游币和个人信息过验证码，请到rrocr.com注册账号并获取appkey"
            ),
        ),
        Divider(),
        InputTag(
            label="个人验证白名单",
            name="开启验证的成员列表",
            value="${开启验证的成员列表}",
            placeholder="输入想启用过验证的qq号",
            enableBatchAdd=True,
            joinValues=False,
            extractValue=True,
            labelRemark=Remark(shape="circle", content="用于签到，米游币和个人信息等过验证码的白名单qq配置"),
        ),
        InputTag(
            label="群组验证白名单",
            name="开启验证的群列表",
            value="${开启验证的群列表}",
            placeholder="输入想启用过验证的群号",
            enableBatchAdd=True,
            joinValues=False,
            extractValue=True,
            labelRemark=Remark(shape="circle", content="用于签到，米游币和个人信息等过验证码的白名单群组配置"),
        ),
        Divider(),
        Switch(
            label='验证米游社签到开关',
            name='米游社自动签到开关',
            value='${米游社自动签到开关}',
            onText='开启',
            offText='关闭'
        ),
        InputTime(
            label='验证米游社自动签到开始时间',
            name='米游社签到开始时间',
            value='${米游社签到开始时间}',
            labelRemark=Remark(shape='circle', content='会在每天这个时间点进行米游社自动签到任务，修改后重启生效'),
            inputFormat='HH时mm分',
            format='HH:mm'
        ),
        Divider(),
        Switch(
            label='验证米游币自动获取开关',
            name='米游币自动获取开关',
            value='${米游币自动获取开关}',
            onText='开启',
            offText='关闭'
        ),
        InputTime(
            label='验证米游币自动获取开始时间',
            name='米游币开始执行时间',
            value='${米游币开始执行时间}',
            labelRemark=Remark(shape='circle', content='会在每天这个时间点进行米游币自动获取任务，修改后重启生效'),
            inputFormat='HH时mm分',
            format='HH:mm'
        ),
    ],
    actions=action_button,
)
tips = Alert(
    level="info",
    body=Html(
        html='显示不全请刷新网页,本插件<a href="https://github.com/forchannot/LittlePaimon-plugin-Captcha" '
        'target="_blank">仓库地址</a>有问题请提issues'
    ),
)
page = PageSchema(
    url="/abyss/configs",
    icon="fa fa-cube",
    label="原神验证签到",
    schema=Page(
        title="原神验证签到",
        initApi="/LittlePaimon/api/abyss_config_g",
        body=[tips, coding_form],
    ),
)

admin_app.pages[0].children.append(page)
