# AutoDL 一键续费脚本

## 📦 依赖管理

- 第三方依赖：
    - `python-dotenv`：用于加载环境变量
    - `selenium`：用于浏览器自动化操作

安装命令：

```bash
pip install python-dotenv selenium
```

## 🚀 运行脚本

运行脚本命令：

```bash
python auto_renew.py
```

## 📝 使用说明

1. 创建一个名为 `.env` 的文件，并添加你的账号和密码(格式如下）
```.env
AUTODL_USERNAME=1234567
AUTODL_PASSWORD=sadfkioixcv
```
2. 运行脚本。
3. 浏览器会自动打开，输入你的账号和密码，然后点击登录。

脚本会自动填写表单，并点击续费按钮。如果成功，脚本会打印出成功信息，否则会打印出错误信息。
脚本已经添加了异常处理，如果发生错误，脚本会打印出错误信息。