# bili-script-tool

一个面向 **B 站视频文案提取** 的开源小工具。  
它不是媒体处理大平台，目标很直接：**尽快把视频变成可用文字**。

核心策略也很克制：

1. 先拿现成字幕
2. 没字幕再下载音频
3. 最后用本地 Whisper 转写

## 功能

- 优先提取官方字幕或自动字幕
- 没字幕时自动回退到 Whisper 转写
- 提供 Windows 图形界面
- 提供命令行版本，适合脚本化使用
- 输出清洗后的 `*.transcript.txt`
- 支持可选 cookies，用于登录后可见视频

## 适合谁

- 想把 B 站视频快速转成文字的人
- 想拿到可复制文案做整理、改写、总结的人
- 不想手敲一堆命令的人
- 想把功能接进自己工作流的人

## 快速开始

### 方式 1：运行图形界面

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
python app.py
```

### 方式 2：使用命令行

```bat
pip install -r requirements.txt
python cli.py "https://www.bilibili.com/video/BV..."
```

安装后也可以直接运行：

```bat
bili-script "https://www.bilibili.com/video/BV..."
```

## Windows 打包成 exe

推荐先用文件夹版：

```bat
build_exe.bat
```

产物位置：

```text
dist\BiliTranscriptTool\BiliTranscriptTool.exe
```

如果你非要单文件：

```bat
build_onefile.bat
```

产物位置：

```text
dist\BiliTranscriptTool.exe
```

## 命令行示例

最基础：

```bat
python cli.py "https://www.bilibili.com/video/BV..."
```

指定输出目录和模型：

```bat
python cli.py "https://www.bilibili.com/video/BV..." -o outputs --model small --device cpu
```

关闭自动转写：

```bat
python cli.py "https://www.bilibili.com/video/BV..." --no-transcribe
```

带 cookies：

```bat
python cli.py "https://www.bilibili.com/video/BV..." --cookie-file cookies.txt
```

## 开发

安装开发依赖：

```bat
pip install -r requirements-dev.txt
```

跑测试：

```bat
pytest
```

跑 lint：

```bat
ruff check .
```

## 仓库已经补好的开源基础设施

这个版本已经补了：

- `LICENSE`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- GitHub Issue 模板
- Pull Request 模板
- 基础 CI
- `pyproject.toml`
- 单元测试样例
- `.gitignore` / `.editorconfig`

也就是说，这已经不是“能跑的脚本”，而是可以直接发 GitHub 的仓库骨架。

## 当前限制

- 目前只支持 B 站
- 还没做批量队列
- 还没做多平台抽象层
- 复杂场景下，Whisper 仍然比较吃机器

## 路线建议

开源初期别把范围搞炸。  
你现在最该做的是：

- 先把 B 站体验打磨稳
- 把 bug report / issue 流程跑起来
- 再考虑 YouTube
- 最后才碰小红书这类更脆的平台

## 合规说明

请自行遵守相关平台条款、版权要求和你所在地区的法律规范。
