# Movie Data Capture (MDC)

一个自动化的影片元数据刮削和整理工具，用于从多个在线数据源获取影片信息，生成NFO文件，下载封面图片，并按照自定义规则整理影片文件。

## 项目概述

Movie Data Capture 是一个功能强大的影片元数据管理工具，支持从多个数据源自动抓取影片信息，包括标题、演员、导演、剧情简介、标签等，并自动下载封面、剧照等图片资源。该工具特别适合需要管理大量影片文件的用户，可以自动生成符合 Kodi、Jellyfin、Emby 等媒体服务器标准的 NFO 元数据文件。

## 核心功能

### 1. 多数据源支持
- **支持的数据源**：javbus, javdb, fanza, xcity, mgstage, fc2, airav, avsox, jav321, carib, caribpr 等 30+ 数据源
- **智能匹配**：自动从多个数据源查询，选择最佳匹配结果
- **优先级配置**：可自定义数据源查询优先级

### 2. 智能番号识别
- **自动提取番号**：从文件名中智能识别影片番号
- **多种格式支持**：支持有码、无码、FC2、Tokyo Hot 等多种番号格式
- **自定义正则**：支持用户自定义番号提取规则
- **特殊处理**：自动识别多碟影片（CD1、CD2）、硬字幕标记（-C、-CH）

### 3. 元数据管理
- **NFO 文件生成**：生成符合 Kodi/Jellyfin/Emby 标准的 NFO 文件
- **完整信息**：包含标题、演员、导演、发行日期、片长、剧情简介、标签、评分等
- **演员照片**：支持下载演员头像到 .actors 目录
- **多语言支持**：支持繁简转换和多语言翻译

### 4. 图片资源下载
- **封面图片**：自动下载并裁剪封面（poster、fanart、thumb）
- **人脸识别**：使用人脸识别技术智能裁剪封面
- **剧照下载**：支持批量下载 extrafanart 剧照
- **水印添加**：可选添加字幕、无码、4K 等标识水印
- **并行下载**：支持多线程并行下载图片资源

### 5. 文件整理
- **自定义规则**：支持自定义文件命名和目录结构规则
- **三种模式**：
  - 模式 1：刮削模式（移动文件）
  - 模式 2：整理模式（仅整理）
  - 模式 3：分析文件夹模式（不移动文件）
- **链接支持**：支持软链接和硬链接方式
- **失败处理**：自动记录失败文件列表，避免重复处理

### 6. 高级特性
- **翻译功能**：支持 Google、Azure、DeepLX 翻译引擎
- **剧情简介增强**：从多个中文数据源获取详细剧情简介
- **代理支持**：支持 HTTP、SOCKS5 代理
- **批量处理**：支持多线程批量处理大量文件
- **增量更新**：支持跳过最近处理过的文件
- **调试模式**：详细的日志输出，便于问题排查

## 工作流程

### 主流程图

```
开始
  ↓
读取配置文件 (config.ini)
  ↓
扫描源文件夹
  ↓
过滤文件列表
  ├─ 跳过失败列表中的文件
  ├─ 跳过最近更新的 NFO
  ├─ 过滤媒体文件类型
  └─ 应用自定义正则过滤
  ↓
遍历每个影片文件
  ↓
┌─────────────────────────────────┐
│ 1. 番号识别 (number_parser.py)  │
│    - 从文件名提取番号            │
│    - 应用自定义正则规则          │
│    - 处理特殊格式                │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ 2. 元数据获取 (scraper.py)      │
│    - 按优先级查询数据源          │
│    - 获取影片详细信息            │
│    - 演员映射和信息映射          │
│    - 翻译处理                    │
│    - 繁简转换                    │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ 3. 文件整理 (core.py)           │
│    - 创建目标文件夹              │
│    - 生成 NFO 文件               │
│    - 下载封面图片                │
│    - 人脸识别裁剪                │
│    - 添加水印                    │
│    - 下载剧照                    │
│    - 下载演员照片                │
│    - 下载字幕                    │
│    - 移动/链接影片文件           │
└─────────────────────────────────┘
  ↓
处理成功？
  ├─ 是 → 移动到成功文件夹
  └─ 否 → 记录到失败列表
  ↓
继续下一个文件
  ↓
清理空文件夹
  ↓
生成日志报告
  ↓
结束
```

### 详细处理流程

#### 1. 番号识别阶段 (number_parser.py)

```python
文件名: "SSIS-001-C.mp4"
  ↓
移除网站标识: "SSIS-001-C.mp4"
  ↓
移除质量标识: "SSIS-001-C.mp4"
  ↓
移除字幕标识: "SSIS-001"
  ↓
提取番号: "SSIS-001"
  ↓
判断有码/无码
  ↓
返回: "SSIS-001"
```

支持的番号格式：
- 标准格式：`ABC-123`, `ABC123`
- FC2 格式：`FC2-1234567`, `FC2-PPV-1234567`
- Tokyo Hot：`n1234`, `k1234`
- Carib：`123456-789`
- 1Pondo/Muramura：`123456_789`
- 欧美格式：`site.YY.MM.DD`

#### 2. 元数据获取阶段 (scraper.py)

```python
番号: "SSIS-001"
  ↓
遍历数据源优先级列表
  ↓
┌─────────────────────┐
│ 数据源 1: javbus    │
│  - 搜索番号         │
│  - 解析页面         │
│  - 提取信息         │
└─────────────────────┘
  ↓
找到数据？
  ├─ 是 → 继续处理
  └─ 否 → 尝试下一个数据源
  ↓
获取基础信息：
  - 标题
  - 演员列表
  - 导演
  - 发行日期
  - 片长
  - 制作商
  - 系列
  - 标签
  - 封面 URL
  - 剧照 URL
  ↓
演员信息映射 (actor_mapping.py)
  - 处理特殊演员名
  - 应用演员映射表
  ↓
信息文本映射 (actor_mapping.py)
  - 标签映射
  - 标题映射
  - 系列映射
  ↓
翻译处理 (translation.py)
  - 标题翻译
  - 简介翻译
  ↓
繁简转换 (OpenCC)
  - 繁体转简体
  - 简体转繁体
  ↓
生成命名规则
  - 应用 naming_rule
  - 应用 location_rule
  ↓
返回完整 JSON 数据
```

#### 3. 文件整理阶段 (core.py)

```python
获取元数据 JSON
  ↓
创建目标文件夹
  - 应用 location_rule
  - 处理特殊字符
  - 创建目录结构
  ↓
生成 NFO 文件
  - 写入所有元数据
  - 保留原有评分
  - 模式 3 保留原有信息
  ↓
下载封面图片
  ↓
┌─────────────────────────────┐
│ 封面处理 (ImageProcessing)  │
│  - 人脸识别 (face_recognition)│
│  - 智能裁剪                  │
│  - 生成 poster/fanart/thumb  │
└─────────────────────────────┘
  ↓
添加水印 (可选)
  - 字幕标识
  - 无码标识
  - 4K 标识
  - ISO 标识
  ↓
下载剧照 (extrafanart)
  - 并行下载
  - 保存到 extrafanart 目录
  ↓
下载演员照片 (可选)
  - 保存到 .actors 目录
  ↓
下载字幕 (可选)
  ↓
移动/链接影片文件
  ├─ 模式 1: 移动文件
  ├─ 模式 2: 整理文件
  └─ 模式 3: 不移动文件
  ↓
完成
```

## 核心模块说明

### Movie_Data_Capture.py
主程序入口，负责：
- 命令行参数解析
- 配置文件加载
- 文件列表扫描和过滤
- 批量处理调度
- 日志管理
- 更新检查

### config.py
配置管理模块，负责：
- 读取 config.ini 配置文件
- 提供配置项访问接口
- 支持命令行参数覆盖配置
- 配置验证和默认值处理

### number_parser.py
番号识别模块，负责：
- 从文件名提取番号
- 支持多种番号格式
- 自定义正则规则
- 有码/无码判断

### scraper.py
元数据刮削模块，负责：
- 调用各数据源 API
- 数据解析和标准化
- 演员和信息映射
- 翻译和繁简转换
- 生成命名规则

### core.py
核心处理模块，负责：
- 文件夹创建
- NFO 文件生成
- 图片下载和处理
- 文件移动和链接
- 失败处理

### ADC_function.py
辅助功能模块，提供：
- HTTP 请求封装
- 代理支持
- Cookie 管理
- 文件下载
- 并行下载

### scrapinglib/
数据源实现目录，包含：
- 各数据源的具体实现
- API 调用和页面解析
- 数据标准化处理

### ImageProcessing/
图片处理目录，包含：
- 人脸识别 (face-recognition)
- 封面裁剪
- 水印添加

## 配置文件说明

### 主要配置项

```ini
[common]
main_mode = 3                    # 工作模式：1=刮削 2=整理 3=分析文件夹
source_folder = ./               # 源文件夹路径
success_output_folder = JAV_output  # 成功输出文件夹
failed_output_folder = failed    # 失败输出文件夹
link_mode = 0                    # 链接模式：0=移动 1=软链接 2=硬链接
nfo_skip_days = 30              # 跳过最近N天更新的NFO
download_only_missing_images = 1 # 仅下载缺失的图片

[proxy]
switch = 1                       # 代理开关
type = http                      # 代理类型：http/socks5
proxy = 127.0.0.1:7899          # 代理地址
timeout = 20                     # 超时时间
retry = 3                        # 重试次数

[Name_Rule]
location_rule = actor+"/"+number # 文件夹命名规则
naming_rule = number+"-"+title   # 文件命名规则
max_title_len = 50              # 标题最大长度

[priority]
website = javbus,javdb,fanza    # 数据源优先级

[translate]
switch = 1                       # 翻译开关
engine = google-free            # 翻译引擎
target_language = zh_cn         # 目标语言
values = title,outline          # 翻译字段

[face]
locations_model = hog           # 人脸识别模型：hog/cnn
uncensored_only = 1             # 仅对无码封面识别
aspect_ratio = 2.12             # 裁剪宽高比

[extrafanart]
switch = 1                       # 剧照下载开关
parallel_download = 5           # 并行下载线程数
```

## 使用方法

### 基本用法

```bash
# 处理单个文件
python Movie_Data_Capture.py /path/to/movie.mp4

# 处理指定文件夹
python Movie_Data_Capture.py -p /path/to/folder

# 指定工作模式
python Movie_Data_Capture.py -m 3 -p /path/to/folder

# 自定义番号
python Movie_Data_Capture.py /path/to/movie.mp4 -n ABC-123
```

### 高级用法

```bash
# 搜索番号信息（不处理文件）
python Movie_Data_Capture.py -s ABC-123

# 指定数据源
python Movie_Data_Capture.py -w javdb -p /path/to/folder

# 覆盖配置项
python Movie_Data_Capture.py -C "debug_mode:switch=1;face:aspect_ratio=2"

# 仅显示处理列表（不实际操作）
python Movie_Data_Capture.py -z -p /path/to/folder

# 强制下载所有图片
python Movie_Data_Capture.py -D -p /path/to/folder

# 无网络操作模式（仅裁剪封面）
python Movie_Data_Capture.py -N -m 3 -p /path/to/folder
```

### 命令行参数

- `-p, --path`: 分析文件夹路径
- `-m, --main-mode`: 主模式 (1/2/3)
- `-n, --number`: 自定义番号
- `-L, --link-mode`: 链接模式 (0/1/2)
- `-w, --website`: 指定数据源
- `-s, --search`: 搜索番号
- `-C, --config-override`: 覆盖配置
- `-D, --download-images`: 强制下载图片
- `-N, --no-network-operation`: 无网络操作
- `-z, --zero-operation`: 仅显示列表
- `-g, --debug`: 调试模式
- `-a, --auto-exit`: 自动退出

## 依赖项

```
requests          # HTTP 请求
dlib-bin          # 人脸识别
numpy             # 数值计算
lxml              # XML 解析
beautifulsoup4    # HTML 解析
pillow            # 图片处理
cloudscraper      # 反爬虫
pysocks           # SOCKS 代理
opencc-python-reimplemented  # 繁简转换
face-recognition-models      # 人脸识别模型
```

## 输出结构

```
JAV_output/
├── 演员名/
│   ├── ABC-123/
│   │   ├── ABC-123.mp4          # 影片文件
│   │   ├── ABC-123.nfo          # 元数据文件
│   │   ├── ABC-123-poster.jpg   # 海报
│   │   ├── ABC-123-fanart.jpg   # 背景图
│   │   ├── ABC-123-thumb.jpg    # 缩略图
│   │   ├── extrafanart/         # 剧照目录
│   │   │   ├── extrafanart-1.jpg
│   │   │   ├── extrafanart-2.jpg
│   │   │   └── ...
│   │   └── .actors/             # 演员照片目录
│   │       ├── 演员1.jpg
│   │       └── 演员2.jpg
│   └── ...
└── ...
```

## 注意事项

1. **代理配置**：访问某些数据源可能需要配置代理
2. **人脸识别**：CNN 模型需要 GPU 支持，HOG 模型速度更快但精度较低
3. **并行下载**：过大的并行数可能导致 IP 被封禁
4. **模式选择**：
   - 模式 1：适合首次整理，会移动文件
   - 模式 2：适合重新整理已有文件
   - 模式 3：适合更新元数据，不移动文件
5. **失败处理**：失败的文件会记录在 `failed/failed_list.txt`
6. **日志文件**：默认保存在 `~/.mlogs/` 目录

## 许可证

本项目遵循开源许可证，详见 LICENSE 文件。

## 免责声明

本工具仅供学习和研究使用，请勿用于非法用途。使用本工具产生的任何后果由使用者自行承担。

---

**版本**: 6.6.7  
**最后更新**: 2024
