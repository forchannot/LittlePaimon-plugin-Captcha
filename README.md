<p align="center" >
  <a href="https://github.com/CMHopeSunshine/LittlePaimon/tree/nonebot2"><img src="https://s1.ax1x.com/2023/02/05/pS62DJK.png" width="256" height="256" alt="LittlePaimon"></a>
</p>
<h1 align="center">LittlePaimon-plugin-Captch</h1>
<h4 align="center">✨仅适用于<a href="https://github.com/CMHopeSunshine/LittlePaimon" target="_blank">LittlePaimon</a>的插件✨</h4>
<p align="center">
    <a href="https://cdn.jsdelivr.net/gh/CMHopeSunshine/LittlePaimon@master/LICENSE"><img src="https://img.shields.io/github/license/CMHopeSunshine/LittlePaimon" alt="license"></a>
    <img src="https://img.shields.io/badge/Python-3.8+-yellow" alt="python">
    <a href="https://qun.qq.com/qqweb/qunpro/share?_wv=3&_wwv=128&inviteCode=MmWrI&from=246610&biz=ka"><img src="https://img.shields.io/badge/QQ频道交流-尘世闲游-blue?style=flat-square" alt="QQ guild"></a>
</p>

<!-- TOC -->
  * [简介](#丨简介)
  * [功能示例](#-功能示例)
  * [安装方法和注意事项](#-安装方法和注意事项)
      * [安装方法：](#安装方法)
      * [注意事项（重要！！！）：](#注意事项)
  * [配置文件](#-配置文件)
  * [鸣谢](#丨鸣谢)
  * [一些个人~~写~~（维护）的插件](#丨-其他插件)
<!-- TOC -->

## 丨简介

用于小派蒙机器人中加强签到的小插件（功能和原版一致，只是加强了一点点）

（由于之前硬性修改[LittlePaimon](https://github.com/CMHopeSunshine/LittlePaimon)源码导致更新容易大面积冲突故产生此插件~悲）

## | 功能示例
使用命令和小派蒙本身的签到命令一致，如果想更改命令，可自行更改`__init__.py`文件

## | 安装方法和注意事项
#### |安装方法：
方法1、将本项目直接clone或者下载压缩包到小派蒙根目录（也就是和`bot.py`同级目录下），在`bot.py`文件中找到`nonebot.load_plugin("LittlePaimon")`这一行，在这一行的下面添加`nonebot.load_plugin("LittlePaimon-plugin-Captcha")`即可

方法2、将本项目直接clone或者下载压缩包到`LittlePaimon\plugins\`内即可

***请注意***，不要直接将本项目放在src/plugins内，否则会导致启动报错！

#### |❗注意事项：
**由于本项目的命令和小派蒙本身的命令相同，有如下两种解决方式：**

1、自行修改命令，修改`__init__.py`文件中的`on_command`后的命令响应内容（即）插件命令为你自己喜欢的命令防止后续更新[小派蒙](https://github.com/CMHopeSunshine/LittlePaimon)本体时冲突~~（我懒得改了）~~

2、将
`LittlePaimon/Plugins/Paimon_AutoBBS`和`LittlePaimon/Plugins/Paimon_DailyNote`的文件夹分别更名为`__Paimon_AutoBBS`和`__Paimon_DailyNote`使得nonebot不加载小派蒙本体的该插件

**强烈建议用方法1自己改命令！！！**

**ps:如果使用本方法，请在涉及到这两个文件夹下有代码更新时将文件夹名改回来!**

## | ⚙️配置文件

启动机器人后进入到小派蒙的后台可在首页看到`原神验证签到`，所有和本插件有关的内容都在里面配置。

**tips**：如果你因为某些原因无法进入后台，可在config/Captcha_config.yml文件中自行设置，但需要注意格式需要符合**yml文件标准**，下面给出了一份参考格式：


	米游币验证自动获取开关: true
	米游币验证开始执行时间(小时): 16
	米游币验证开始执行时间(分钟): 0
	米游社验证自动签到开关: true
	米游社验证签到开始时间(小时): 0
	米游社验证签到开始时间(分钟): 5
	实时便签验证检查开关: true
	实时便签验证停止检查开始时间: 8
	实时便签验证停止检查结束时间: 13
	实时便签验证检查间隔: 14
	打码平台: false
	第三方链接: '123'
	人人打码appkey: '44'
	开启验证的成员列表:
	- 1231
	- 414
	开启验证的群列表:
	- 123143
	- 1
	- 2


## 丨💸鸣谢

* [LittlePaimon](https://github.com/CMHopeSunshine/LittlePaimon)实时便签和米游币获取代码

* [GenshinUID](https://github.com/KimigaiiWuyi/GenshinUID/tree/nonebot2-beta1)签到代码

* [LittlePaimon-plugin-Abyss](https://github.com/CM-Edelweiss/LittlePaimon-plugin-Abyss)（本项目和该项目基本相同，除了判断方法外）



## 丨 其他插件

[原神模拟圣遗物](https://github.com/forchannot/nonebot_plugin_artifact)