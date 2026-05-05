# cbhpacks MCP 工具集成 - 文档索引

欢迎使用 cbhpacks MCP 工具包！本文档索引帮助你快速找到所需信息。

---

## 📚 文档列表

### 1. [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) ⭐ **推荐首先阅读**
**快速参考卡** - 最常用的工具选择指南和快捷命令

**适合场景**:
- ✅ 第一次使用，想快速上手
- ✅ 忘记某个参数怎么设置
- ✅ 查找常用工作流模板
- ✅ 需要故障排查帮助

**内容包括**:
- 场景→工具推荐对照表
- 常用工作流代码模板
- 参数速查表
- 输出文件位置图
- 快捷命令集合
- 故障排查指南

---

### 2. [CBHPACKS_MCP_TOOL_GUIDE.md](./CBHPACKS_MCP_TOOL_GUIDE.md)
**工具使用指南** - 每个工具的详细使用说明

**适合场景**:
- ✅ 需要了解某个工具的完整参数
- ✅ 查看详细的返回值说明
- ✅ 学习单个工具的具体用法

**内容包括**:
- 25 个 cbhpacks 工具的详细说明
- 每个工具的完整参数列表
- 返回值格式说明
- 使用示例代码

---

### 3. [MCP_TOOLS_COMPLETE_LIST.md](./MCP_TOOLS_COMPLETE_LIST.md)
**完整工具清单** - 所有 MCP 工具的全面文档

**适合场景**:
- ✅ 想了解项目支持的所有工具
- ✅ 对比基础工具和 cbhpacks 工具
- ✅ 查看完整的工具分类体系
- ✅ 学习完整建模流程

**内容包括**:
- 6 个基础工具说明（包括 execute_code_tool）
- 25 个 cbhpacks 工具详解
- 工具分类体系
- 完整建模流程示例
- 输出文件说明

---

### 4. [CBHPACKS_INTEGRATION_SUMMARY.md](./CBHPACKS_INTEGRATION_SUMMARY.md)
**集成总结** - 项目开发总结和源码映射

**适合场景**:
- ✅ 了解项目的整体架构
- ✅ 查看 cbhpacks 源码与 MCP 工具的映射关系
- ✅ 理解工具的设计思路
- ✅ 验证工具覆盖完整性

**内容包括**:
- 完成工作总结
- 源文件到工具的完整映射表
- 工具使用策略（含 execute_code_tool 的定位）
- 技术亮点和后续建议

---

## 🎯 快速导航

### 按使用阶段

#### 新手入门
1. 先看 [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - 快速了解能做什么
2. 再看 [CBHPACKS_MCP_TOOL_GUIDE.md](./CBHPACKS_MCP_TOOL_GUIDE.md) - 学习具体工具用法
3. 参考 [MCP_TOOLS_COMPLETE_LIST.md](./MCP_TOOLS_COMPLETE_LIST.md) - 了解完整能力

#### 日常开发
- 📖 [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - 查找参数和模板
- 💻 [CBHPACKS_MCP_TOOL_GUIDE.md](./CBHPACKS_MCP_TOOL_GUIDE.md) - 查看详细 API

#### 深入学习
- 🏗️ [CBHPACKS_INTEGRATION_SUMMARY.md](./CBHPACKS_INTEGRATION_SUMMARY.md) - 理解架构设计
- 📋 [MCP_TOOLS_COMPLETE_LIST.md](./MCP_TOOLS_COMPLETE_LIST.md) - 研究完整流程

### 按查询需求

| 我想知道... | 查看文档 | 章节 |
|------------|---------|------|
| 某个场景用哪个工具？ | QUICK_REFERENCE.md | 场景 → 推荐工具 |
| 工具的参数有哪些？ | CBHPACKS_MCP_TOOL_GUIDE.md | 各工具说明 |
| 如何开始一个建模项目？ | QUICK_REFERENCE.md | 常用工作流 |
| 输出文件在哪里？ | QUICK_REFERENCE.md | 输出文件位置 |
| execute_code_tool 怎么用？ | MCP_TOOLS_COMPLETE_LIST.md | 基础工具部分 |
| 某个 cbhpacks 函数对应哪个 MCP 工具？ | CBHPACKS_INTEGRATION_SUMMARY.md | 源码映射 |
| 项目总共有多少工具？ | CBHPACKS_INTEGRATION_SUMMARY.md | 工具统计 |
| 出错了怎么办？ | QUICK_REFERENCE.md | 故障排查 |

---

## 📊 工具概览

### 工具总数：31 个

- **基础工具**: 6 个（python-mcp-notebook 原有）
- **cbhpacks 工具**: 25 个（新增封装）

### cbhpacks 工具分类

| 分类 | 工具数 | 代表工具 |
|------|-------|---------|
| 数据生成 | 1 | generate_random_data |
| 分箱分析 | 3 | create_bins_report, get_psi_report |
| 特征选择 | 3 | feature_selection, recursive_feature_selection |
| 特征编码 | 1 | encode_features |
| 模型训练 | 2 | train_binary_model, generate_model_report |
| 无监督学习 | 2 | pca_analysis, kmeans_clustering |
| 回归分析 | 1 | linear_regression |
| 描述统计 | 2 | descriptive_statistics, single_column_analysis |
| 特征工程 | 2 | rfms_feature_engineering |
| 数据库操作 | 5 | query_clickhouse, query_hive |
| Linux 操作 | 1 | execute_linux_command |
| 文件传输 | 2 | upload_file, download_file |

---

## 🔧 核心文件

| 文件 | 作用 | 大小 |
|------|------|------|
| `cbhpacks_mcp_tools.py` | MCP 工具定义文件 | 42KB |
| `mcp_server.py` | MCP 服务器（已添加 cbhpacks 工具注册） | 13KB |
| `cbhpacks/__init__.py` | cbhpacks 模块导出 | 1.5KB |

---

## 🚀 快速启动

```bash
# 进入项目目录
cd /media/chenbh17/cbhssd/python-mcp-notebook-Copy1

# 启动 MCP 服务
python mcp_server.py

# 看到以下输出表示成功：
# cbhpacks MCP tools registered successfully!
```

---

## 💡 使用建议

### 推荐优先级

1. **专用 cbhpacks 工具** - 开箱即用，自动保存报告
2. **execute_code_tool** - 定制化分析，cbhpacks 未覆盖场景
3. **基础工具** - 文件管理、环境配置等辅助功能

### execute_code_tool 的正确用法

`execute_code_tool` 是一个万能工具，当你需要：
- ✅ cbhpacks 专用工具未覆盖的定制化分析
- ✅ 快速原型开发和测试
- ✅ 直接调用 cbhpacks 模块的底层 API
- ✅ 数据探索和可视化
- ✅ 安装额外的 Python 包

示例：
```python
execute_code_tool(code="""
from cbhpacks.bins_model import bins_model
import pandas as pd

df = pd.read_csv('/workspace/data.csv')
bm = bins_model(df=df, cols=['col1','col2'], group=10, target='target', 
                 nan=-9999, bins_type='eq_cnt', path='/workspace/output')
woe_data, iv_data = bm.comp_woe_iv()
print('自定义分析完成！')
""")
```

---

## 📞 支持与反馈

如遇到问题或有改进建议：
1. 先查阅相关文档的"故障排查"章节
2. 检查 QUICK_REFERENCE.md 中的常见问题
3. 查看 MCP_TOOLS_COMPLETE_LIST.md 确认工具参数

---

## 📝 版本信息

- **cbhpacks 版本**: 1.0.0
- **集成日期**: 2026-03-29
- **工具数量**: 25 个 cbhpacks 工具 + 6 个基础工具
- **文档版本**: 1.0

---

**祝你使用愉快！** 🎉
