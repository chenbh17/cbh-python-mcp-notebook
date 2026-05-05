# Python MCP Notebook - 完整工具清单

## 概述

本项目包含两大类 MCP 工具：
1. **基础工具**：python-mcp-notebook 原生提供的工具
2. **cbhpacks 工具**：从 cbhpacks 代码包封装的数据科学与机器学习工具

---

## 一、基础工具（原有）

### 1. Python 代码执行

#### `execute_code_tool`
执行任意 Python 代码（**万能工具，用于 cbhpacks 未覆盖的场景**）
- **参数**: 
  - `code`: Python 代码字符串
- **返回**: 
  - `success`: 执行是否成功
  - `output`: 标准输出
  - `error`: 错误信息（如果有）
- **使用场景**:
  - cbhpacks 专用工具未覆盖的定制化分析
  - 快速原型开发和测试
  - 直接调用 cbhpacks 模块
  - 数据探索和可视化
  - 安装额外的 Python 包
- **示例 1 - 直接使用 cbhpacks 模块**:
```python
execute_code_tool(code="""
from cbhpacks.bins_model import bins_model
import pandas as pd

df = pd.read_csv('/workspace/data.csv')
bm = bins_model(df=df, cols=['col1','col2'], group=10, target='target', 
                 nan=-9999, bins_type='eq_cnt', path='/workspace/output')
woe_data, iv_data = bm.comp_woe_iv()
print(f'IV 值：{iv_data}')
""")
```
- **示例 2 - 自定义分析**:
```python
execute_code_tool(code="""
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('/workspace/data.csv')
df.describe().to_excel('/workspace/desc_stats.xlsx')
df['target'].value_counts().plot(kind='bar')
plt.savefig('/workspace/target_dist.png')
print('分析完成！')
""")
```
- **示例 3 - 安装并使用新包**:
```python
# 先安装包
install_package_tool(package='scikit-learn')

# 使用包
execute_code_tool(code="""
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

iris = load_iris()
clf = RandomForestClassifier(n_estimators=100)
clf.fit(iris.data, iris.target)
print(f'模型准确率：{clf.score(iris.data, iris.target)}')
""")
```

### 2. 系统管理

#### `health_check_tool`
健康检查
- **参数**: 无
- **返回**: `{"status": "healthy"}`

#### `install_package_tool`
安装 Python 包
- **参数**: 
  - `package`: 包名称
- **返回**: 安装结果

#### `execute_terminal_command_tool`
执行终端命令
- **参数**: 
  - `command`: Shell 命令
- **返回**: 命令执行结果

### 3. 文件管理

#### `list_files_tool`
列出目录中的文件
- **参数**: 
  - `path`: 路径（相对于/workspace）
- **返回**: 文件列表（包含文件名、类型、大小、修改时间）

#### `get_download_link_tool`
获取文件下载链接
- **参数**: 
  - `filepath`: 文件路径
- **返回**: 下载链接 URL

---

## 二、cbhpacks 数据科学工具

### 1. 数据生成

#### `generate_random_data`
生成随机测试数据集
- **参数**:
  - `min_edge`: 随机整数最小值
  - `max_edge`: 随机整数最大值
  - `num`: 数据行数
  - `mth_cnt`: 月份数量
- **返回**: 数据表信息、预览、保存路径
- **源码对应**: `cbhpacks/models_for_try.py::get_random_data`

### 2. 分箱与 WOE 转换

#### `create_bins_report`
生成分箱报告（WOE、IV、KS、Lift 等）
- **参数**:
  - `data_file_path`: 输入 CSV 文件路径
  - `cols`: 特征列名列表
  - `target`: 目标变量列名
  - `group`: 分箱数量
  - `nan_value`: 缺失值填充值
  - `bins_type`: 分箱类型 (eq_cnt, eq_distance, deci_tree_bin, chi2_bin, cat_bin)
  - `adj_bin`: 是否调整分箱
  - `output_dir`: 输出目录名
- **返回**: WOE 报告、IV 报告路径及摘要
- **源码对应**: `cbhpacks/bins_model.py::bins_model.comp_woe_iv`

#### `transform_to_woe`
将数据转换为 WOE 编码
- **参数**: 同 `create_bins_report`
- **返回**: WOE 转换后数据、映射字典
- **源码对应**: `cbhpacks/bins_model.py::bins_model.data_to_woe`

#### `get_psi_report`
计算 PSI（群体稳定性指标）报告
- **参数**:
  - `data_file_path`: 输入 CSV 文件路径
  - `cols`: 特征列名列表
  - `mth_col`: 月份列名
  - `base_mth`: 基准月份
  - `cmp_mth`: 比较月份
  - `bins_type`: 分箱类型
  - `group`: 分箱数量
  - `target`: 目标变量
  - `nan_value`: 缺失值填充值
  - `output_dir`: 输出目录名
- **返回**: PSI 单月报告、PSI 均值报告
- **源码对应**: `cbhpacks/bins_model.py::bins_model.get_psi & psi_mth_avg`

### 3. 特征选择

#### `feature_selection`
多方法特征选择
- **参数**:
  - `data_file_path`: 输入 CSV 文件路径
  - `cols`: 候选特征列表
  - `target`: 目标变量
  - `selection_methods`: 筛选方法列表 (null, enumerate, iv, psi, corr, chi2, logistic, ml, vif)
  - `null_pct`: 缺失值阈值
  - `iv_thres`: IV 阈值
  - `corr_thres`: 相关系数阈值
  - `psi_thres`: PSI 阈值
  - `output_dir`: 输出目录名
- **返回**: 筛选后的特征列表、各方法筛选详情
- **源码对应**: `cbhpacks/cols_select.py::cols_select` 系列方法

#### `bootstrap_feature_selection`
Bootstrap 特征选择（有放回抽样评估重要性）
- **参数**:
  - `data_file_path`: 输入 CSV 文件路径
  - `cols`: 候选特征列表
  - `target`: 目标变量
  - `num_iterations`: Bootstrap 迭代次数
  - `frac`: 抽样比例
  - `boot_thres`: 重要性阈值
  - `boot_method`: 模型方法 (lgb, xgb, rdf)
  - `output_dir`: 输出目录名
- **返回**: 筛选后的特征、重要性数据
- **源码对应**: `cbhpacks/cols_select.py::cols_select.boostrap_select`

#### `recursive_feature_selection`
递归特征选择（迭代筛选）
- **参数**:
  - `train_data_path`: 训练数据路径
  - `test_data_path`: 测试数据路径
  - `cols`: 候选特征列表
  - `target`: 目标变量
  - `method`: 模型方法 (xgb, lgb)
  - `recursion_num`: 递归迭代次数
  - `stay_pct`: 每次迭代保留比例
  - `output_dir`: 输出目录名
- **返回**: 最终选择的特征、迭代数据
- **源码对应**: `cbhpacks/cols_select.py::cols_select_js.recursion_select`

### 4. 特征编码

#### `encode_features`
特征编码（多种编码方式）
- **参数**:
  - `data_file_path`: 输入 CSV 文件路径
  - `cols`: 需要编码的特征列表
  - `encode_type`: 编码类型 (minmax, sc, sigmoid, softmax, bins, count, woe)
  - `target`: 目标变量（WOE 编码时需要）
  - `group`: 分箱数量
  - `nan_value`: 缺失值填充值
  - `bins_type`: 分箱类型
  - `output_dir`: 输出目录名
- **返回**: 编码后数据文件路径
- **源码对应**: `cbhpacks/cols_encode.py::cols_encode` 系列方法

### 5. 模型训练与评估

#### `train_binary_model`
训练二分类模型（支持 6 种模型）
- **参数**:
  - `train_data_path`: 训练数据路径
  - `test_data_path`: 测试数据路径
  - `cols`: 特征列表
  - `target`: 目标变量
  - `model_type`: 模型类型 (lr, xgb, lgbm, mlp, svm, rdf)
  - `model_params`: 模型参数字典
  - `output_dir`: 输出目录名
- **返回**: 模型路径、训练信息
- **源码对应**: `cbhpacks/model_training.py::binary_model` 系列 fit 方法

#### `generate_model_report`
生成模型评估报告
- **参数**:
  - `model_path`: 模型所在目录
  - `group`: 评分分箱数量
  - `bins_type`: 分箱类型 (all, eq_cnt, eq_distance)
  - `mth_col`: 月份列名
  - `base_mth`: 基准月份
- **返回**: AUC、KS 等评估指标、报告文件路径
- **源码对应**: `cbhpacks/model_training.py::binary_model.report`

### 6. 无监督学习

#### `pca_analysis`
主成分分析 (PCA)
- **参数**:
  - `data_file_path`: 输入 CSV 文件路径
  - `cols`: 特征列表
  - `mean_key`: 主键列表
  - `target`: 目标变量
  - `var_ratio_cumsum`: 累计方差解释比例阈值
  - `output_dir`: 输出目录名
- **返回**: 主成分列表、降维数据
- **源码对应**: `cbhpacks/model_training.py::uns_model.pca`

#### `kmeans_clustering`
K-Means 聚类分析
- **参数**:
  - `data_file_path`: 输入 CSV 文件路径
  - `cols`: 特征列表
  - `n_clusters`: 聚类个数
  - `output_dir`: 输出目录名
- **返回**: 聚类标签、簇中心
- **源码对应**: `cbhpacks/model_training.py::uns_model.kmeans`

### 7. 回归分析

#### `linear_regression`
线性回归分析（OLS、Logit、工具变量回归）
- **参数**:
  - `data_file_path`: 输入 CSV 文件路径
  - `cols`: 解释变量列表
  - `target`: 被解释变量
  - `iv_target`: 工具变量回归的目标列
  - `iv_col`: 工具变量列
  - `output_dir`: 输出目录名
- **返回**: 模型摘要、显著性检验结果
- **源码对应**: `cbhpacks/model_training.py::linear_model`

### 8. 描述统计

#### `descriptive_statistics`
描述性统计分析
- **参数**:
  - `data_file_path`: 输入 CSV 文件路径
  - `cols`: 需要分析的特征列表
  - `cat_cols`: 离散型特征列表
  - `output_dir`: 输出目录名
- **返回**: 数值型和分类型特征统计报告
- **源码对应**: `cbhpacks/preprocess.py::desc_df.get_rpt`

#### `single_column_analysis`
单变量详细分析（描述性、相关性、有监督、异常值检测）
- **参数**:
  - `data_file_path`: 输入 CSV 文件路径
  - `col`: 要分析的单个特征
  - `cols`: 所有特征列表
  - `target`: 目标变量
  - `cat_cols`: 离散型特征列表
  - `corr_threshold`: 相关性阈值
  - `output_dir`: 输出目录名
- **返回**: 分析报告、图表路径
- **源码对应**: `cbhpacks/preprocess.py::desc_col.feat_card`

### 9. 特征工程

#### `rfms_feature_engineering`
RFMS 范式特征衍生（滚动窗口统计特征）
- **参数**:
  - `data_file_path`: 输入 CSV 文件路径
  - `cols`: 需要衍生的特征列表
  - `origin_table`: 原始 Hive 表名
  - `new_table`: 新生成的 Hive 表名
  - `day_list`: 时间窗口列表
- **返回**: 新表名、衍生特征数量
- **源码对应**: `cbhpacks/con_sql.py::rfms_sql`

#### `create_hive_table`
生成 Hive 建表语句
- **参数**:
  - `data_file_path`: 数据文件路径
  - `table_name`: Hive 表名
  - `partition`: 是否分区
  - `bucket`: 是否分桶
  - `partition_col`: 分区列
  - `bucket_col`: 分桶列
  - `bucket_num`: 分桶数量
  - `encoding`: 编码格式
- **返回**: 建表 SQL 语句
- **源码对应**: `cbhpacks/con_sql.py::get_create_table`

### 10. 数据库操作

#### `query_clickhouse`
ClickHouse 数据库查询
- **参数**: `sql` - SQL 查询语句
- **返回**: 查询结果
- **源码对应**: `cbhpacks/con_sql.py::chdf`

#### `execute_clickhouse`
ClickHouse SQL 执行（INSERT、CREATE 等）
- **参数**: `sql` - SQL 执行语句
- **返回**: 执行结果
- **源码对应**: `cbhpacks/con_sql.py::chrun`

#### `query_mysql`
MySQL 数据库查询
- **参数**:
  - `sql`: SQL 查询语句
  - `host`: MySQL 服务器地址
  - `port`: MySQL 端口
  - `user`: 用户名
  - `password`: 密码
  - `database`: 数据库名
- **返回**: 查询结果
- **源码对应**: `cbhpacks/con_sql.py::con_mysql`

#### `query_hive`
Hive 数据库查询
- **参数**:
  - `sql`: SQL 查询语句
  - `host`: Hive 服务器地址
  - `port`: Hive 端口
  - `username`: 用户名
  - `password`: 密码
  - `database`: 数据库名
- **返回**: 查询结果
- **源码对应**: `cbhpacks/con_sql.py::con_hive`

#### `save_to_hive`
将数据保存到 Hive 表
- **参数**:
  - `data_file_path`: 本地数据文件路径
  - `table_name`: Hive 表名
  - `local_loc`: 本地文件保存路径
  - `method`: 写入方式 (overwrite, append)
  - `encoding`: 文件编码
  - `partition`: 是否分区
  - `partition_col`: 分区列
- **返回**: 保存结果
- **源码对应**: `cbhpacks/con_sql.py::to_hive`

### 11. Linux 操作

#### `execute_linux_command`
在 Linux 服务器上执行 Shell 命令
- **参数**:
  - `shell`: Shell 命令
  - `user`: 登录用户 (chenbh17 或 root)
- **返回**: 命令执行结果
- **源码对应**: `cbhpacks/con_linux.py::con_linux`

### 12. 文件传输

#### `upload_file`
上传本地文件到 Docker 容器工作目录
- **参数**:
  - `local_file_path`: 本地文件路径（宿主机）
  - `container_file_path`: 容器目标路径（相对于/workspace）
- **返回**: 上传结果

#### `download_file`
从 Docker 容器下载文件到本地
- **参数**:
  - `container_file_path`: 容器文件路径（相对于/workspace）
  - `local_file_path`: 本地目标路径
- **返回**: 下载结果

---

## 三、工具使用流程示例

### 完整建模流程

```python
# 1. 生成随机数据
result = generate_random_data(min_edge=1, max_edge=100, num=10000, mth_cnt=12)

# 2. 描述性统计分析
result = descriptive_statistics(
    data_file_path="/workspace/random_data_10000rows.csv",
    output_dir="desc_stats"
)

# 3. 分箱分析
result = create_bins_report(
    data_file_path="/workspace/random_data_10000rows.csv",
    cols=['col1','col2','col3','col4'],
    target='target',
    group=10,
    bins_type='eq_cnt'
)

# 4. 特征选择
result = feature_selection(
    data_file_path="/workspace/random_data_10000rows.csv",
    cols=['col1','col2','col3','col4'],
    target='target',
    selection_methods=['null', 'iv', 'corr', 'chi2'],
    output_dir="feature_selection"
)

# 5. WOE 转换
result = transform_to_woe(
    data_file_path="/workspace/random_data_10000rows.csv",
    cols=['col1','col2','col3'],
    target='target',
    output_dir="woe_transform"
)

# 6. 训练 LightGBM 模型
result = train_binary_model(
    train_data_path="/workspace/train.csv",
    test_data_path="/workspace/test.csv",
    cols=['col1','col2','col3'],
    target='target',
    model_type='lgbm',
    output_dir="binary_model"
)

# 7. 生成模型评估报告
result = generate_model_report(
    model_path="/workspace/binary_model",
    group=30
)
```

---

## 四、输出文件说明

所有工具生成的文件都保存在 `/workspace` 目录下：

| 工具类别 | 输出目录 | 主要文件 |
|---------|---------|---------|
| 分箱分析 | `bins_result/` | WOE 报告、IV 报告、分箱详情 |
| 特征选择 | `feature_selection/` | 筛选特征列表、相关性矩阵、VIF 详情 |
| 特征编码 | `feature_encoding/` | 编码后数据、编码映射字典 |
| 模型训练 | `binary_model/` | 模型文件、评估报告、KS/AUC曲线图 |
| PCA 分析 | `pca_analysis/` | 主成分数据、降维结果 |
| 聚类分析 | `kmeans_clustering/` | 聚类标签、簇中心 |
| 描述统计 | `desc_stats/` | 数值型/分类型特征统计报告 |
| 单变量分析 | `single_col_analysis/` | 单变量分析报告、图表 |
| Bootstrap 选择 | `bootstrap_selection/` | 重要性数据、筛选结果 |
| 递归选择 | `recursive_selection/` | 迭代数据、最佳特征组合 |
| PSI 报告 | `psi_report/` | PSI 单月报告、PSI 均值报告 |

---

## 五、注意事项

1. **文件路径**: 所有文件路径使用绝对路径，相对于 `/workspace` 目录
2. **数据格式**: 输入数据应为 CSV 格式，包含表头
3. **目标变量**: 二分类任务的目标变量应为 0/1 格式
4. **缺失值处理**: 建议使用统一的缺失值标识（如 -9999）
5. **数据库连接**: 数据库工具需要预先配置好连接信息
6. **模型训练**: 建议先进行特征选择和编码，再训练模型
