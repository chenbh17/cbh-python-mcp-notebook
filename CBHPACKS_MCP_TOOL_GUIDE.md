# cbhpacks MCP 工具使用指南

## 概述

cbhpacks MCP 工具包已将 cbhpacks 模块中的所有功能封装为 MCP 工具，可通过 MCP 协议调用。

## 工具列表

### 1. 数据生成工具

#### `generate_random_data`
生成随机测试数据表
- **参数**:
  - `min_edge`: 随机整数最小值
  - `max_edge`: 随机整数最大值
  - `num`: 数据行数
  - `mth_cnt`: 月份数量
- **返回**: 生成的数据表信息（列名、行数、预览）

### 2. 数据分箱工具

#### `create_bins_report`
生成分箱报告（WOE、IV、KS 等）
- **参数**:
  - `data_file_path`: 输入数据文件路径 (CSV)
  - `cols`: 需要分箱的特征列名列表
  - `target`: 目标变量列名
  - `group`: 分箱数量 (默认 10)
  - `nan_value`: 缺失值填充值 (默认 -9999)
  - `bins_type`: 分箱类型 (eq_cnt, eq_distance, deci_tree_bin, chi2_bin, cat_bin)
  - `adj_bin`: 是否调整分箱 (默认 False)
  - `output_dir`: 输出目录名
- **返回**: 分箱结果信息（WOE 报告、IV 报告路径）

#### `transform_to_woe`
将数据转换为 WOE 编码
- **参数**: 同 `create_bins_report`
- **返回**: WOE 转换结果（转换后数据、映射字典）

### 3. 特征选择工具

#### `feature_selection`
特征选择工具，支持多种筛选方法
- **参数**:
  - `data_file_path`: 输入数据文件路径
  - `cols`: 候选特征列名列表
  - `target`: 目标变量列名
  - `selection_methods`: 筛选方法列表 (null, enumerate, iv, psi, corr, chi2, logistic, ml, vif)
  - `null_pct`: 缺失值阈值 (默认 0.95)
  - `iv_thres`: IV 阈值 (默认 0.01)
  - `corr_thres`: 相关系数阈值 (默认 0.8)
  - `psi_thres`: PSI 阈值 (默认 0.1)
  - `output_dir`: 输出目录名
- **返回**: 特征选择结果（筛选后的特征列表、各方法筛选详情）

### 4. 数据编码工具

#### `encode_features`
特征编码工具
- **参数**:
  - `data_file_path`: 输入数据文件路径
  - `cols`: 需要编码的特征列名列表
  - `encode_type`: 编码类型 (minmax, sc, sigmoid, softmax, bins, count, woe)
  - `target`: 目标变量 (WOE 编码时需要)
  - `group`: 分箱数量 (默认 10)
  - `nan_value`: 缺失值填充值 (默认 -9999)
  - `bins_type`: 分箱类型
  - `output_dir`: 输出目录名
- **返回**: 编码结果（编码后数据文件路径）

### 5. 二分类模型训练工具

#### `train_binary_model`
训练二分类模型（支持 LR、XGBoost、LightGBM、MLP、SVM、随机森林）
- **参数**:
  - `train_data_path`: 训练数据文件路径
  - `test_data_path`: 测试数据文件路径
  - `cols`: 特征列名列表
  - `target`: 目标变量列名
  - `model_type`: 模型类型 (lr, xgb, lgbm, mlp, svm, rdf)
  - `model_params`: 模型参数字典
  - `output_dir`: 输出目录名
- **返回**: 模型训练结果（模型路径、训练信息）

#### `generate_model_report`
生成模型评估报告（混淆矩阵、KS、AUC、LIFT 等）
- **参数**:
  - `model_path`: 模型所在目录路径
  - `group`: 评分分箱数量 (默认 30)
  - `bins_type`: 分箱类型 (all, eq_cnt, eq_distance)
  - `mth_col`: 月份列名
  - `base_mth`: 基准月份
- **返回**: 模型报告（AUC、KS 等评估指标）

### 6. 无监督学习工具

#### `pca_analysis`
主成分分析 (PCA)
- **参数**:
  - `data_file_path`: 输入数据文件路径
  - `cols`: 特征列名列表
  - `mean_key`: 主键列名列表
  - `target`: 目标变量列名
  - `var_ratio_cumsum`: 累计方差解释比例阈值 (默认 0.8)
  - `output_dir`: 输出目录名
- **返回**: PCA 分析结果（主成分、降维数据）

#### `kmeans_clustering`
K-Means 聚类分析
- **参数**:
  - `data_file_path`: 输入数据文件路径
  - `cols`: 特征列名列表
  - `n_clusters`: 聚类个数 (默认 10)
  - `output_dir`: 输出目录名
- **返回**: 聚类结果（聚类标签、簇中心）

### 7. 线性回归工具

#### `linear_regression`
线性回归分析（OLS、Logit、工具变量回归）
- **参数**:
  - `data_file_path`: 输入数据文件路径
  - `cols`: 解释变量列名列表
  - `target`: 被解释变量列名
  - `iv_target`: 工具变量回归的目标列
  - `iv_col`: 工具变量列
  - `output_dir`: 输出目录名
- **返回**: 回归分析结果（模型摘要、显著性检验）

### 8. 数据描述统计工具

#### `descriptive_statistics`
描述性统计分析
- **参数**:
  - `data_file_path`: 输入数据文件路径
  - `cols`: 需要分析的特征列表（可选）
  - `cat_cols`: 离散型特征列表
  - `output_dir`: 输出目录名
- **返回**: 描述统计结果（数值型、分类型特征统计）

### 9. 数据库查询工具

#### `query_clickhouse`
ClickHouse 数据库查询
- **参数**: `sql` - SQL 查询语句
- **返回**: 查询结果

#### `execute_clickhouse`
ClickHouse 执行 SQL（INSERT、CREATE 等）
- **参数**: `sql` - SQL 执行语句
- **返回**: 执行结果

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

#### `save_to_hive`
将数据保存到 Hive 表
- **参数**:
  - `data_file_path`: 本地数据文件路径
  - `table_name`: Hive 表名（需包含库名）
  - `local_loc`: 本地文件保存路径
  - `method`: 写入方式 (overwrite, append)
  - `encoding`: 文件编码
  - `partition`: 是否分区
  - `partition_col`: 分区列
- **返回**: 保存结果

### 10. Linux 命令执行工具

#### `execute_linux_command`
在 Linux 服务器上执行 Shell 命令
- **参数**:
  - `shell`: Shell 命令（可包含多条，用分号分隔）
  - `user`: 登录用户 (chenbh17 或 root)
- **返回**: 命令执行结果

### 11. 文件上传下载工具

#### `upload_file`
上传本地文件到 Docker 容器工作目录
- **参数**:
  - `local_file_path`: 本地文件路径（宿主机路径）
  - `container_file_path`: 容器中目标文件路径（相对于/workspace 目录）
- **返回**: 上传结果

#### `download_file`
从 Docker 容器下载文件到本地
- **参数**:
  - `container_file_path`: 容器中的文件路径（相对于/workspace 目录）
  - `local_file_path`: 本地目标文件路径
- **返回**: 下载结果

## 使用示例

### 示例 1: 生成随机数据并分箱

```python
# 生成随机数据
result = generate_random_data(min_edge=1, max_edge=100, num=1000, mth_cnt=12)

# 分箱分析
result = create_bins_report(
    data_file_path="/workspace/random_data_1000rows.csv",
    cols=['col1', 'col2', 'col3'],
    target='target',
    group=10,
    bins_type='eq_cnt'
)
```

### 示例 2: 特征选择与编码

```python
# 特征选择
result = feature_selection(
    data_file_path="/workspace/data.csv",
    cols=['col1', 'col2', 'col3', 'col4'],
    target='target',
    selection_methods=['null', 'iv', 'corr'],
    output_dir="feature_selection_result"
)

# 特征编码
result = encode_features(
    data_file_path="/workspace/feature_selection_result/selected_data.csv",
    cols=['col1', 'col2', 'col3'],
    encode_type='woe',
    target='target'
)
```

### 示例 3: 训练二分类模型

```python
# 训练 LightGBM 模型
result = train_binary_model(
    train_data_path="/workspace/train.csv",
    test_data_path="/workspace/test.csv",
    cols=['col1', 'col2', 'col3'],
    target='target',
    model_type='lgbm',
    model_params={'n_estimators': 100, 'learning_rate': 0.1}
)

# 生成模型报告
result = generate_model_report(
    model_path="/workspace/binary_model",
    group=30
)
```

### 示例 4: 数据库查询

```python
# ClickHouse 查询
result = query_clickhouse("SELECT * FROM table LIMIT 100")

# MySQL 查询
result = query_mysql(
    sql="SELECT * FROM users WHERE age > 18",
    host='localhost',
    user='root',
    password='password',
    database='test'
)
```

## 输出文件说明

所有工具生成的结果文件都保存在 `/workspace` 目录下的指定输出目录中：

- **分箱报告**: `bins_result/` - 包含 WOE 报告、IV 报告、分箱详情
- **特征选择**: `feature_selection/` - 包含筛选后的特征列表、相关性矩阵、VIF 详情
- **特征编码**: `feature_encoding/` - 包含编码后数据、编码映射字典
- **模型训练**: `binary_model/` - 包含模型文件、评估报告、KS/AUC曲线图
- **PCA 分析**: `pca_analysis/` - 包含主成分数据、降维结果
- **聚类分析**: `kmeans_clustering/` - 包含聚类标签、簇中心
- **描述统计**: `desc_stats/` - 包含数值型和分类型特征统计报告

## 注意事项

1. **文件路径**: 所有文件路径都应使用绝对路径，相对于 `/workspace` 目录
2. **数据格式**: 输入数据应为 CSV 格式，包含表头
3. **目标变量**: 二分类任务的目标变量应为 0/1 格式
4. **缺失值处理**: 建议使用统一的缺失值标识（如 -9999）
5. **数据库连接**: 数据库工具需要预先配置好连接信息
