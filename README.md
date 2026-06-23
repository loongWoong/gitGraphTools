# git-graph — Repository Intelligence Dashboard

> 读取 Git 仓库历史，生成包含健康分析、分支分叉关系、作者贡献、Bus Factor、交互式 Diff 等维度的智能仪表盘。

## 快速开始

```bash
# 静态模式：分析当前仓库，生成独立 HTML 文件
python gitGraphTools/git_graph.py .

# 指定输出路径并自动打开浏览器
python gitGraphTools/git_graph.py . -o dashboard.html --open

# Server 模式：启动本地服务，支持交互式 Diff 查看
python gitGraphTools/git_graph.py . --serve

# 限制最近 200 个 commit（大型仓库推荐）
python gitGraphTools/git_graph.py . -n 200 -o dashboard.html
```

## 两种运行模式

| 模式 | 命令 | 说明 |
|------|------|------|
| **静态模式** | `python git_graph.py .` | 生成独立 `.html` 文件，双击打开。适合分享和归档。 |
| **Server 模式** | `python git_graph.py . --serve` | 启动本地 HTTP 服务（默认 `127.0.0.1:8765`），支持点击 commit 查看变更文件和 Diff。 |

### Server 模式特别功能

点击任意 commit → 右侧面板显示 **Changed Files**（含 `A/M/D` 状态 + `+N -M` 统计），再点击文件 → 展开 **Unified Diff**（增行绿底、删行红底）。

```
┌─ Changed Files ───────────────────────────────────┐
│  M  src/.../BenchmarkController.java    +189 -0   │  ← 点击展开 Diff
│  M  src/.../BenchmarkShadowService.java +174 -0   │
└──────────────────────────────────────────────────┘
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `repo_path` | Git 仓库路径 | `.`（当前目录） |
| `-o, --output` | 输出 HTML 文件路径 | `git_graph.html` |
| `-n, --max-commits` | 限制最近 N 个 commit | 无限制 |
| `--serve` | 启动 Server 模式（支持交互式 Diff） | 否 |
| `--port` | Server 端口（配合 `--serve` 使用） | `8765` |
| `--open` | 生成后自动在浏览器中打开 | 否 |
| `--version` | 显示版本号 | — |

## 五大视图

### 1. Overview（概览）

打开后的默认页面，一览仓库全局状态：

- **指标卡片**：Commit 总数、分支数、贡献者数、僵尸分支数
- **健康仪表盘**：仓库整体健康评分（0-100），环形进度条 + 状态分布
- **Top Branches**：最活跃的分支列表，含 commit 数、作者数、健康状态色点
- **Needs Attention**：僵尸/废弃/已合并未删除分支，含具体警告信息
- **Quick Actions**：可操作的分支清理建议

### 2. Graph（结构图）

经典的 Git DAG 可视化，采用 **focus-mode 渲染**：

- **分支高亮**：点击左侧图例或图中分支标签 → 该分支全亮，其余淡化至 8%，图自动平滑滚动定位到分支位置
- **悬停 Tooltip**：显示 hash、subject、作者、日期，**以及所属分支列表（含健康状态色点）**
- **点击详情**：右侧滑出面板，展示完整 commit message、parents、children、**分支标签（含僵尸/废弃状态标注）**
- **Changed Files + Diff**（Server 模式）：详情面板底部展示变更文件列表，点击文件展开 Unified Diff
- **搜索过滤**：按 hash / subject / author 实时过滤，显示匹配数量
- **右下角小地图**：全局缩略图，点击跳转
- **键盘快捷键**：

| 按键 | 功能 |
|------|------|
| `+` / `-` | 缩放 |
| `F` | 适应窗口 |
| `Esc` | 清除选择 / 清除搜索 |
| 鼠标拖拽 | 平移 |
| 鼠标滚轮 | 缩放（以鼠标位置为中心） |

### 3. Timeline（时间线 / 分叉关系图）

在绝对时间轴上展示分支的分叉和合并关系，**只展示关键节点**（分叉点和 tip），忽略中间提交：

```
main     ○─────────────────────────────────────○
               \                /
benchmark      ○────────────────○
               \                 \
0604-nlq        ○─────────────────○
                      \            /
hermes                ○───────────○
```

- **日期标尺**：顶部按月显示时间刻度
- **水平线**：分支存活期，颜色对应健康状态；已合并分支显示虚线
- **空心圆点 ○**：分叉点（从父分支分出的位置）
- **实心圆点 ●**：分支 tip（最后提交）
- **斜向虚线**：从父分支到子分支的分叉关系
- **点击分支名**：跳转到 Graph 视图并高亮该分支
- **"Show merged" 复选框**：切换是否显示已合并分支
- **底部 Heatmap**：GitHub 风格的周提交热力图

### 4. Authors（作者）

- **Author Contributions**：每位贡献者的 commit 数、占比、活跃时间范围
- **Bus Factor Warnings**：标记单人多于 80% 贡献的文件，显示风险等级

### 5. AI Insights（AI 洞察）

预留视图，后续支持接入 LLM，按需生成分支摘要和版本说明。

## 主题切换

右上角 `☼` 按钮切换暗色 / 亮色主题，选择自动保存到 `localStorage`，刷新后保持。

- **暗色主题**（默认）：GitHub Dark（`#0d1117` 底色）
- **亮色主题**：GitHub Light（`#ffffff` 底色）

## 分支健康算法

工具自动识别分支类型并采用**差异化权重**评分：

| 分支类型 | 识别规则 | 评分特点 |
|----------|----------|----------|
| `main` | main / master | 不考核活跃度、不考核存活时长 |
| `release/*` | release/ 前缀 | 允许长期存活（180 天内不扣分） |
| `feature/*` | feature/、feat/ 前缀 | 严格考核时效（建议 < 60 天） |
| `hotfix/*` | hotfix/、fix/、bugfix/ 前缀 | 最严格时效（建议 < 7 天） |

### 分支健康等级

| 状态 | 颜色 | 含义 | 建议操作 |
|------|------|------|----------|
| 🟢 Healthy | 绿 `#238636` | 活跃且健康 | 继续开发 |
| 🟡 Aging | 金 `#d29922` | 开始老化 | 关注进度 |
| 🟣 Merged Zombie | 紫 `#8957e5` | 已合入 main，60+ 天未更新 | 可以删除 |
| 🔴 Abandoned Zombie | 红 `#f85149` | 未合入 main，90+ 天未更新 | 需要评审 |
| ⚪ Merged Stale | 灰 `#6e7681` | 已合入，短期停滞 | 可以删除 |

## Server 模式 API 端点

当使用 `--serve` 启动时，提供以下 API：

| 端点 | 方法 | 返回 | 对应 Git 命令 |
|------|------|------|---------------|
| `/` | GET | Dashboard HTML | — |
| `/api/files/<hash>` | GET | `{files: [{path, status, added, deleted}]}` | `git diff-tree --numstat` |
| `/api/diff/<hash>` | GET | `{diff: "unified diff"}` | `git show --patch` |
| `/api/diff/<hash>?file=<path>` | GET | `{diff: "single file diff"}` | `git show --patch -- <path>` |

## 技术架构

```
git log --all     git for-each-ref     git branch --merged
      ↓                  ↓                     ↓
  git_reader.py      git_reader.py        git_reader.py
      ↓                  ↓                     ↓
  ┌────────────── data_model.py ──────────────────┐
  │  Commit / BranchInfo / Edge / GraphData       │
  └───────────────────────────────────────────────┘
      ↓          ↓           ↓             ↓
  layout_engine  health      temporal      author
  (DAG + lanes)  analyzer    analyzer      analyzer
      ↓          ↓           ↓             ↓
  ┌────────── html_builder.py ────────────────────┐
  │  多视图 JSON 序列化                            │
  └───────────────────────────────────────────────┘
      ↓                               ↓
  __template__.py              server.py (--serve)
  静态 HTML                    按需 git 查询
```

- **零外部依赖**：仅使用 Python 标准库 + 系统 Git 命令
- **完全离线**（静态模式）：生成的 HTML 内嵌所有 CSS/JS，不加载外部资源（字体除外）
- **单文件输出**：一个 `.html` 文件包含所有视图

## 文件结构

```
gitGraphTools/
  pyproject.toml                  # 项目元数据
  git_graph.py                    # CLI 入口
  git_graph/
    __init__.py
    git_reader.py                 # Git 子进程调用封装
    data_model.py                 # 数据模型与解析
    layout_engine.py              # DAG 拓扑排布算法
    health_analyzer.py            # 分支健康评分 + 僵尸检测
    temporal_analyzer.py          # 热力图 + 时间线分叉关系数据
    author_analyzer.py            # 作者统计 + Bus Factor
    server.py                     # HTTP Server（--serve 模式）
    html_builder.py               # JSON → HTML
    __template__.py               # HTML/CSS/JS 模板
```

## 设计原则

1. **信息密度克制**：默认首页只展示概览卡片 + 核心指标，详情按需展开
2. **结构/时间分离**：Graph（结构视图）和 Timeline（时间视图）使用不同坐标系，不混合
3. **Timeline 精简**：只展示分叉点和 tip，忽略中间提交，聚焦分支关系
4. **角色自适应评分**：不同分支类型使用不同健康标准，避免误判
5. **色盲友好**：绿/金/紫/灰四色区分状态，不使用红绿搭配
6. **焦点模式渲染**：选中分支高亮，其余淡化，类似 VSCode Explorer
7. **亮/暗双主题**：右上角一键切换，偏好持久化

## 兼容性

- **Python**: 3.8+
- **Git**: 2.0+
- **浏览器**: Chrome 90+, Firefox 90+, Safari 15+, Edge 90+
