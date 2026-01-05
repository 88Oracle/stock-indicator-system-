# 📦 项目Git发布指南

**项目名称**: TA-Lib指标计算与性能优化系统
**更新日期**: 2026-01-01
**适用平台**: Gitee / GitHub

---

## 📋 目录

1. [前期准备](#前期准备)
2. [方案A: 发布到Gitee（推荐国内用户）](#方案a-发布到gitee)
3. [方案B: 发布到GitHub](#方案b-发布到github)
4. [后续维护](#后续维护)
5. [常见问题](#常见问题)

---

## 前期准备

### 1. 检查Git是否已安装

```bash
git --version
```

如果未安装，请下载：
- **Windows**: https://git-scm.com/download/win
- **Gitee推荐**: https://gitee.com/help/articles/4106

### 2. 配置Git用户信息（首次使用）

```bash
# 设置用户名
git config --global user.name "你的名字"

# 设置邮箱
git config --global user.email "your-email@example.com"

# 查看配置
git config --list
```

### 3. 项目文件检查

确保以下文件存在且完整：

```
D:\shixun\project\
├── .gitignore          # Git忽略规则（已创建）
├── README.md           # 项目说明（重要！）
├── requirements.txt    # Python依赖
├── src/                # 源代码
├── tests/              # 测试代码
├── docs/               # 文档
└── data/               # 数据文件（大文件会被忽略）
```

---

## 方案A: 发布到Gitee

### 优势
- ✅ 国内访问速度快
- ✅ 界面中文友好
- ✅ 适合团队协作
- ✅ 私有仓库免费

### Step 1: 注册Gitee账号

1. 访问 https://gitee.com/
2. 点击右上角"注册"
3. 填写手机号/邮箱完成注册

### Step 2: 创建远程仓库

#### 方式1: 网页创建（推荐）

1. 登录Gitee，点击右上角 **"+"** → **"新建仓库"**

2. 填写仓库信息：
   ```
   仓库名称: stock-indicator-system
   路径: stock-indicator-system
   仓库介绍: 基于Polars的高性能股票技术指标计算系统
   是否开源: 选择"公开"或"私有"
   初始化: 不要勾选（我们本地已有代码）
   ```

3. 点击 **"创建"**

4. 记录仓库地址（例如）：
   ```
   https://gitee.com/你的用户名/stock-indicator-system.git
   ```

#### 方式2: 命令行创建

```bash
# 需要先安装Gitee CLI工具
# 访问 https://gitee.com/help/articles/4122
```

### Step 3: 本地初始化Git仓库

打开命令行，进入项目目录：

```bash
cd D:\shixun\project

# 1. 初始化Git仓库
git init

# 2. 添加所有文件
git add .

# 3. 查看状态（确认文件已添加）
git status

# 4. 提交到本地仓库
git commit -m "初始提交: 完成性能优化，提升52%速度"

# 5. 重命名主分支为main（可选，Gitee默认是master）
git branch -M main
```

### Step 4: 连接远程仓库并推送

```bash
# 1. 添加远程仓库（替换为你的仓库地址）
git remote add origin https://gitee.com/你的用户名/stock-indicator-system.git

# 2. 推送到远程仓库
git push -u origin main

# 或者如果使用master分支
# git push -u origin master
```

**首次推送需要输入Gitee用户名和密码**

### Step 5: 验证发布成功

访问你的Gitee仓库地址，应该能看到所有文件：
```
https://gitee.com/你的用户名/stock-indicator-system
```

---

## 方案B: 发布到GitHub

### 优势
- ✅ 全球最大开源社区
- ✅ 适合开源项目
- ✅ 丰富的生态工具
- ✅ GitHub Pages支持

### Step 1: 注册GitHub账号

1. 访问 https://github.com/
2. 点击 **"Sign up"** 注册
3. 完成邮箱验证

### Step 2: 创建远程仓库

1. 登录GitHub，点击右上角 **"+"** → **"New repository"**

2. 填写仓库信息：
   ```
   Repository name: stock-indicator-system
   Description: High-performance stock indicator calculation system based on Polars
   Public / Private: 选择公开或私有
   Initialize: 不要勾选（本地已有代码）
   ```

3. 点击 **"Create repository"**

4. 记录仓库地址：
   ```
   https://github.com/你的用户名/stock-indicator-system.git
   ```

### Step 3-5: 同Gitee方案

本地初始化和推送步骤完全相同，只需替换远程仓库地址：

```bash
cd D:\shixun\project
git init
git add .
git commit -m "Initial commit: Performance optimization completed, 52% faster"
git branch -M main
git remote add origin https://github.com/你的用户名/stock-indicator-system.git
git push -u origin main
```

**注意**: GitHub可能需要使用Personal Access Token代替密码。

#### 创建GitHub Token（如果需要）

1. 登录GitHub → Settings → Developer settings
2. Personal access tokens → Generate new token
3. 勾选 `repo` 权限
4. 生成Token并保存（只显示一次！）
5. 推送时用Token作为密码

---

## 📝 完整操作脚本

### Windows PowerShell / CMD

```bash
# 进入项目目录
cd D:\shixun\project

# 初始化Git
git init

# 添加所有文件
git add .

# 查看要提交的文件
git status

# 提交到本地
git commit -m "初始提交: 完成性能优化，包含110个指标，速度提升52%"

# 重命名分支
git branch -M main

# 添加远程仓库（Gitee示例，GitHub同理）
git remote add origin https://gitee.com/你的用户名/stock-indicator-system.git

# 推送到远程
git push -u origin main
```

### 如果遇到"远程仓库已存在"错误

```bash
# 删除现有远程仓库
git remote remove origin

# 重新添加
git remote add origin https://gitee.com/你的用户名/stock-indicator-system.git

# 再次推送
git push -u origin main
```

---

## 🔄 后续维护

### 1. 日常提交流程

```bash
# 查看修改的文件
git status

# 添加修改的文件
git add .
# 或添加特定文件
git add src/core/data_processor.py

# 提交到本地
git commit -m "优化: 添加LazyFrame支持，提升10%性能"

# 推送到远程
git push
```

### 2. 提交信息规范

建议使用以下前缀：

- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构
- `perf:` 性能优化
- `test:` 测试相关
- `chore:` 构建/工具

示例：
```bash
git commit -m "feat: 添加LazyFrame延迟执行支持"
git commit -m "fix: 修复CSV读取编码问题"
git commit -m "docs: 更新性能测试报告"
git commit -m "perf: 优化Parquet保存速度，提升34%"
```

### 3. 查看提交历史

```bash
# 查看提交日志
git log

# 查看简洁日志
git log --oneline

# 查看最近3次提交
git log -3
```

### 4. 创建分支（可选）

```bash
# 创建并切换到新分支
git checkout -b feature/lazy-frame

# 开发完成后合并到main
git checkout main
git merge feature/lazy-frame

# 推送分支到远程
git push origin feature/lazy-frame
```

---

## ⚠️ 重要注意事项

### 1. 大文件处理

**问题**: Git不适合管理大文件（>100MB）

**数据文件处理**:
```bash
# 数据文件已在.gitignore中忽略
# 如果已经添加，需要移除：
git rm --cached data/通达信数据_20251229.csv
git rm --cached data/*.duckdb
```

**推荐方案**:
- 大数据文件：使用网盘分享（百度网盘、阿里云盘）
- 在README.md中说明数据获取方式
- 使用Git LFS（大文件存储）：https://git-lfs.github.com/

### 2. 敏感信息

确保不要提交：
- 数据库密码
- API密钥
- 个人隐私信息

**如果已提交**:
```bash
# 从历史中完全删除（危险操作，谨慎使用）
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/sensitive-file" \
  --prune-empty --tag-name-filter cat -- --all
```

### 3. .gitignore说明

已创建的`.gitignore`会忽略：
- Python缓存 (`__pycache__`, `*.pyc`)
- 虚拟环境 (`.venv/`)
- IDE配置 (`.idea/`, `.vscode/`)
- 数据库文件 (`*.duckdb`)
- 输出结果 (`output/results/`)

---

## 📚 常见问题

### Q1: 推送时要求输入用户名密码？

**Gitee**:
- 用户名: Gitee登录名
- 密码: Gitee登录密码

**GitHub**:
- 用户名: GitHub用户名
- 密码: Personal Access Token（不是登录密码！）

### Q2: 推送失败提示"Permission denied"？

**解决方案**:

1. 检查仓库地址是否正确
2. 检查是否有仓库权限
3. 尝试使用HTTPS而非SSH：
   ```bash
   git remote set-url origin https://gitee.com/你的用户名/stock-indicator-system.git
   ```

### Q3: 如何删除远程仓库上的文件？

```bash
# 删除远程文件但保留本地
git rm --cached 文件名
git commit -m "移除不需要的文件"
git push
```

### Q4: 如何查看远程仓库地址？

```bash
git remote -v
```

### Q5: 推送时提示"文件太大"？

GitHub限制单个文件<100MB，仓库<1GB。

**解决方案**:
1. 检查并移除大文件
2. 使用`.gitignore`忽略大文件
3. 使用Git LFS管理大文件

### Q6: 如何回退到之前的版本？

```bash
# 查看历史
git log --oneline

# 回退到指定版本（保留修改）
git reset --soft 版本号

# 回退到指定版本（丢弃修改，谨慎！）
git reset --hard 版本号

# 推送到远程（需要强制推送）
git push -f
```

---

## 🎯 推荐的仓库结构

确保你的仓库包含以下关键文件：

```
stock-indicator-system/
├── README.md                 # ✅ 项目说明（必需）
├── requirements.txt          # ✅ 依赖清单
├── .gitignore               # ✅ 忽略规则
├── LICENSE                  # 📄 开源协议（可选）
├── docs/                    # 📚 文档目录
│   ├── 性能优化指南.md
│   ├── 快速优化成果报告.md
│   └── 指标参考手册.md
├── src/                     # 💻 源代码
│   ├── core/
│   ├── config/
│   └── scripts/
├── tests/                   # 🧪 测试代码
└── output/                  # 📊 输出（大文件忽略）
```

---

## 📖 推荐阅读

- **Git官方教程**: https://git-scm.com/book/zh/v2
- **Gitee帮助中心**: https://gitee.com/help
- **GitHub Docs**: https://docs.github.com/
- **Git简明指南**: https://rogerdudler.github.io/git-guide/index.zh.html

---

## ✅ 快速检查清单

发布前确认：

- [ ] 已创建`.gitignore`文件
- [ ] 已配置Git用户信息
- [ ] README.md内容完整
- [ ] requirements.txt准确
- [ ] 移除了敏感信息
- [ ] 移除了大文件
- [ ] 在Gitee/GitHub创建了远程仓库
- [ ] 成功推送到远程仓库
- [ ] 在网页上确认文件完整

---

## 🚀 立即开始

### 最快发布流程（5分钟）

```bash
# 1. 进入项目目录
cd D:\shixun\project

# 2. 初始化并提交
git init
git add .
git commit -m "初始提交: 高性能股票指标计算系统"
git branch -M main

# 3. 在Gitee/GitHub网页创建仓库，然后：
git remote add origin https://gitee.com/你的用户名/stock-indicator-system.git
git push -u origin main

# 完成！
```

---

**发布成功后，记得在README.md中添加仓库徽章！**

```markdown
[![Gitee](https://gitee.com/你的用户名/stock-indicator-system/badge/star.svg)](https://gitee.com/你的用户名/stock-indicator-system)
```

**祝发布顺利！** 🎉
