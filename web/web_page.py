from amis import (
    Action,
    Alert,
    Divider,
    Form,
    Group,
    Html,
    InputNumber,
    InputTag,
    InputText,
    InputTime,
    InputTimeRange,
    LevelEnum,
    Page,
    PageSchema,
    Remark,
    Select,
    Switch,
)
from LittlePaimon.web.pages import admin_app

action_button = [
    Action(label="保存", level=LevelEnum.success, type="submit"),
    Action(label="重置", level=LevelEnum.warning, type="reset"),
]
coding_form = Form(
    title="过验证码配置",
    name="abyss_config",
    api="post:/LittlePaimon/api/abyss_config",
    body=[
        Group(
            mode="horizontal",
            labelWidth="auto",
            body=[
                Select(
                    label="ssbq打码平台选择",
                    name="ssbq打码平台",
                    value="${ssbq打码平台}",
                    labelRemark=Remark(shape="circle", content="选择ssbq的打码平台"),
                    options=[
                        {"label": "人人", "value": "rr"},
                        {"label": "第三方", "value": "sf"},
                        {"label": "套套", "value": "tt"},
                    ],
                ),
                Select(
                    label="米游社签到打码平台选择",
                    name="米游社签到打码平台",
                    value="${米游社签到打码平台}",
                    labelRemark=Remark(shape="circle", content="选择米游社签到的打码平台"),
                    options=[
                        {"label": "人人", "value": "rr"},
                        {"label": "第三方", "value": "sf"},
                        {"label": "套套", "value": "tt"},
                    ],
                ),
                Select(
                    label="米游币打码平台选择",
                    name="米游币获取打码平台",
                    value="${米游币获取打码平台}",
                    labelRemark=Remark(shape="circle", content="选择米游币获取的打码平台"),
                    options=[
                        {"label": "人人", "value": "rr"},
                        {"label": "第三方", "value": "sf"},
                        {"label": "套套", "value": "tt"},
                    ],
                ),
            ],
        ),
        Group(
            mode="horizontal",
            labelWidth="auto",
            body=[
                InputText(
                    label="第三方请求链接",
                    name="第三方链接",
                    value="${第三方链接}",
                    placeholder="输入第三方平台的打码请求链接(需包含token值),以&结束",
                    labelRemark=Remark(
                        shape="circle",
                        content="例如：http(s)://abc.bb?token=xxx&,或者http("
                        "s)://abc.bb/token=xxx&，具体请看第三方平台api",
                    ),
                ),
                InputText(
                    label="人人appkey",
                    name="人人打码appkey",
                    value="${人人打码appkey}",
                    placeholder="输入你在人人打码获取的appkey",
                    labelRemark=Remark(
                        shape="circle",
                        content="用于签到，米游币和个人信息过验证码，请到rrocr.com注册账号并获取appkey",
                    ),
                ),
                InputText(
                    label="套套appkey",
                    name="套套打码appkey",
                    value="${套套打码appkey}",
                    placeholder="输入你在套套打码获取的appkey",
                    labelRemark=Remark(
                        shape="circle",
                        content="用于签到，米游币和个人信息过验证码，请到http://www.ttocr.com/user/index.html注册账号并获取appkey",
                    ),
                ),
            ],
        ),
        Divider(),
        Group(
            mode="horizontal",
            labelWidth="auto",
            body=[
                InputTag(
                    label="个人验证白名单",
                    name="开启验证的成员列表",
                    value="${开启验证的成员列表}",
                    placeholder="输入想启用过验证的qq号",
                    enableBatchAdd=True,
                    joinValues=False,
                    extractValue=True,
                    labelRemark=Remark(
                        shape="circle", content="用于签到，米游币和个人信息等过验证码的白名单qq配置"
                    ),
                ),
                InputTag(
                    label="群组验证白名单",
                    name="开启验证的群列表",
                    value="${开启验证的群列表}",
                    placeholder="输入想启用过验证的群号",
                    enableBatchAdd=True,
                    joinValues=False,
                    extractValue=True,
                    labelRemark=Remark(
                        shape="circle", content="用于签到，米游币和个人信息等过验证码的白名单群组配置"
                    ),
                ),
            ],
        ),
        Divider(),
        Group(
            mode="horizontal",
            labelWidth="auto",
            body=[
                Switch(
                    label="米游社验证自动签到开关",
                    name="米游社验证自动签到开关",
                    value="${米游社验证自动签到开关}",
                    onText="开启",
                    offText="关闭",
                ),
                InputTime(
                    label="米游社验证签到开始时间",
                    name="米游社验证签到开始时间",
                    value="${米游社验证签到开始时间}",
                    labelRemark=Remark(
                        shape="circle", content="会在每天这个时间点进行米游社自动签到任务，修改后重启生效"
                    ),
                    inputFormat="HH时mm分",
                    format="HH:mm",
                ),
            ],
        ),
        Divider(),
        Group(
            mode="horizontal",
            labelWidth="auto",
            body=[
                Switch(
                    label="星铁自动签到验证开关",
                    name="星铁自动签到验证开关",
                    value="${星铁自动签到验证开关}",
                    onText="开启",
                    offText="关闭",
                ),
                InputTime(
                    label="星铁签到验证开始执行时间",
                    name="星铁签到验证开始执行时间",
                    value="${星铁签到验证开始执行时间}",
                    labelRemark=Remark(
                        shape="circle", content="会在每天这个时间点进行星铁自动签到任务，修改后重启生效"
                    ),
                    inputFormat="HH时mm分",
                    format="HH:mm",
                ),
            ],
        ),
        Divider(),
        Group(
            mode="horizontal",
            labelWidth="auto",
            body=[
                Switch(
                    label="米游币验证自动获取开关",
                    name="米游币验证自动获取开关",
                    value="${米游币验证自动获取开关}",
                    onText="开启",
                    offText="关闭",
                ),
                InputTime(
                    label="米游币验证开始执行时间",
                    name="米游币验证开始执行时间",
                    value="${米游币验证开始执行时间}",
                    labelRemark=Remark(
                        shape="circle", content="会在每天这个时间点进行米游币自动获取任务，修改后重启生效"
                    ),
                    inputFormat="HH时mm分",
                    format="HH:mm",
                ),
            ],
        ),
        Divider(),
        Group(
            mode="horizontal",
            labelWidth="auto",
            body=[
                Switch(
                    label="实时便签验证检查开关",
                    name="实时便签验证检查开关",
                    value="${实时便签验证检查开关}",
                    labelRemark=Remark(
                        shape="circle", content="开启检查实时便签,用于体力溢出检测,不建议开启"
                    ),
                    onText="开启",
                    offText="关闭",
                ),
                InputTimeRange(
                    label="实时便签验证停止检查时间段",
                    name="实时便签验证停止检查时间段",
                    value="${实时便签验证停止检查时间段}",
                    labelRemark=Remark(
                        shape="circle",
                        content="在这段时间(例如深夜)不进行实时便签检查，注意开始时间不要晚于结束时间，不然会有问题",
                    ),
                    timeFormat="HH",
                    format="HH",
                    inputFormat="HH时",
                ),
                InputNumber(
                    label="实时便签验证检查间隔",
                    name="实时便签验证检查间隔",
                    value="${实时便签验证检查间隔}",
                    labelRemark=Remark(
                        shape="circle",
                        content="每多少分钟检查进行一次实时便签，推荐不快于8分钟，修改后重启生效",
                    ),
                    displayMode="enhance",
                    suffix="分钟",
                    min=1,
                ),
            ],
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
