# NatterWeb


[![LICENSE](https://img.shields.io/github/license/mashape/apistatus.svg?style=flat-square&label=LICENSE)](https://github.com/maytom2016/NatterWeb/blob/master/LICENSE)
![GitHub Stars](https://img.shields.io/github/stars/maytom2016/NatterWeb.svg?style=flat-square&label=Stars&logo=github)
![GitHub Forks](https://img.shields.io/github/forks/maytom2016/NatterWeb.svg?style=flat-square&label=Forks&logo=github)

## 介绍
Natter的套壳WEB UI。本程序是一个名为Natter的Web图形用户界面（GUI），用于将位于全锥形NAT（网络地址转换）后的端口暴露到互联网。

## Natter介绍
[https://github.com/MikeWang000000/Natter](https://github.com/MikeWang000000/Natter)

## 安装
~~~
git clone  https://github.com/maytom2016/NatterWeb.git
~~~
~~~
pip install -r requirements.txt
~~~
## 启动
~~~
python3 app.py
~~~
## 参数
### 1. --version或-V

作用：显示Natter Web的版本信息。

示例：在命令行中输入python app.py -V或者python app.py --version，程序将输出类似Natter Web <版本号>的版本信息。

### 2. -r
作用：在程序启动时运行已启用的Natter规则。

示例：如果在命令行输入python app.py -r，程序启动时会运行相关规则。

### 3. -t

默认值：0.0.0.0。

作用：指定程序监听的IP地址。

示例：如果要将监听地址设置为192.168.1.100，可以在命令行输入python app.py -t 192.168.1.100。

### 4. -p

默认值：18650。

作用：指定程序监听的端口号。

示例：若想将监听端口设置为8080，在命令行输入python your_program.py -p 8080即可。

## 关于插件及开发说明

本项目目前内置了一个插件，功能是通过邮件通知公网IP映射变动。本质上是嵌入了一个fastapi的应用，若想开发类似应用，可以看/plugin/notification了解细节。

### 细节提示：
shared_vars.py这个文件可以获取到主应用的运行信息，包括任务数、应用启动情况等。

class BaseConfig:定义这个类可以把嵌入的应用放到主程序的导航栏上。

使用主程序变量时，应当通过线程锁等方式保持线程同步，防止异常行为。

目录结构为/plugin/插件目录/插件所需资源(jinja2模板、静态js脚本文件、css排版等)及py文件。

