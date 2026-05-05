# cbhpacks MCP 工具快速参考卡

## 工具选择指南

### 🎯 场景 → 推荐工具

| 场景 | 推荐工具 | 替代方案 |
|------|---------|---------|
| **生成测试数据** | `generate_random_data` | `execute_code_tool` |
| **分箱分析 (WOE/IV)** | `create_bins_report` | `execute_code_tool` + `bins_model` |
| **PSI 稳定性指标** | `get_psi_report` | `execute_code_tool` + `bins_model` |
| **特征选择 (多方法)** | `feature_selection` | `execute_code_tool` + `cols_select` |
| **Bootstrap 特征选择** | `bootstrap_feature_selection` | `execute_code_tool` + `cols_select.boostrap_select` |
| **递归特征选择** | `recursive_feature_selection` | `execute_code_tool` + `cols_select_js` |
| **特征编码** | `encode_features` | `execute_code_tool` + `cols_encode` |
| **训练二分类模型** | `train_binary_model` | `execute_code_tool` + `binary_model` |
| **模型评估报告** | `generate_model_report` | `execute_code_tool` + `binary_model.report` |
| **PCA 降维** | `pca_analysis` | `execute_code_tool` + `uns_model.pca` |
| **K-Means 聚类** | `kmeans_clustering` | `execute_code_tool` + `uns_model.kmeans` |
| **线性回归** | `linear_regression` | `execute_code_tool` + `linear_model` |
| **描述性统计** | `descriptive_statistics` | `execute_code_tool` + `desc_df` |
| **单变量详细分析** | `single_column_analysis` | `execute_code_tool` + `desc_col` |
| **RFMS 特征衍生** | `rfms_feature_engineering` | `execute_code_tool` + `rfms_sql` |
| **Hive 建表** | `create_hive_table` | `execute_code_tool` + `get_create_table` |
| **ClickHouse 查询** | `query_clickhouse` | `execute_code_tool` + `chdf` |
| **MySQL 查询** | `query_mysql` | `execute_code_tool` + `con_mysql` |
| **Hive 查询** | `query_hive` | `execute_code_tool` + `con_hive` |
| **保存到 Hive** | `save_to_hive` | `execute_code_tool` + `to_hive` |
| **Linux 命令** | `execute_linux_command` | `execute_code_tool` + `con_linux` |
| **文件上传** | `upload_file` | - |
| **文件下载** | `download_file` | `get_download_link_tool` |
| **自定义分析** | `execute_code_tool` | - |

---

## 常用工作流

### 1️⃣ 标准建模流程

```python
# Step 1: 生成/加载数据
generate_random_data(min_edge=1, max_edge=100, num=10000, mth_cnt=12)

# Step 2: 探索性分析
descriptive_statistics(data_file_path="/workspace/data.csv")

# Step 3: 分箱与 WOE 转换
create_bins_report(data_file_path="/workspace/data.csv", cols=cols, target='target')
transform_to_woe(data_file_path="/workspace/data.csv", cols=cols, target='target')

# Step 4: 特征选择
feature_selection(data_file_path="/workspace/data.csv", cols=cols, target='target',
                  selection_methods=['null', 'iv', 'corr'])

# Step 5: 模型训练
train_binary_model(train_data_path="/workspace/train.csv", 
                   test_data_path="/workspace/test.csv",
                   cols=selected_cols, target='target', model_type='lgbm')

# Step 6: 模型评估
generate_model_report(model_path="/workspace/binary_model", group=30)
```

### 2️⃣ 快速原型开发（使用 execute_code_tool）

```python
execute_code_tool(code="""
from cbhpacks.bins_model import bins_model
from cbhpacks.model_training import binary_model
import pandas as pd

# 读取数据
df = pd.read_csv('/workspace/data.csv')

# 快速分箱
bm = bins_model(df=df, cols=['col1','col2'], group=10, target='target',
                nan=-9999, bins_type='eq_cnt', path='/workspace/quick_test')
woe_data, iv_data = bm.comp_woe_iv()

# 快速建模
train, test = train_test_split(df, test_size=0.2)
mt = binary_model(train=train, test=test, cols=['col1','col2'], 
                  target='target', model_path='/workspace/quick_model')
mt.lgbm_fit(n_estimators=100)
mt.report(group=10)

print('快速原型完成！')
""")
```

### 3️⃣ 数据库驱动的分析

```python
# Step 1: 从 ClickHouse 查询数据
query_clickhouse(sql="SELECT * FROM features WHERE mth >= 202401 LIMIT 100000")

# Step 2: 特征工程
rfms_feature_engineering(data_file_path="/workspace/query_result.csv",
                         cols=['col1','col2','col3'],
                         origin_table='db.source_table',
                         new_table='db.derived_table')

# Step 3: 保存回 Hive
save_to_hive(data_file_path="/workspace/result.csv",
             table_name='db.result_table',
             local_loc='/tmp/result.csv')
```

---

## 参数速查

### 分箱相关参数

| 参数 | 含义 | 常用值 |
|------|------|--------|
| `bins_type` | 分箱类型 | `eq_cnt`(等频), `eq_distance`(等距), `deci_tree_bin`(决策树), `chi2_bin`(卡方) |
| `group` | 分箱数量 | 5-20 |
| `adj_bin` | 是否调整分箱 | True/False |
| `nan_value` | 缺失值标识 | -9999, -1, 0 |

### 特征选择相关参数

| 参数 | 含义 | 常用值 |
|------|------|--------|
| `selection_methods` | 筛选方法 | `['null', 'iv', 'corr', 'chi2']` |
| `null_pct` | 缺失值阈值 | 0.95 |
| `iv_thres` | IV 阈值 | 0.01-0.03 |
| `corr_thres` | 相关性阈值 | 0.7-0.8 |
| `psi_thres` | PSI 阈值 | 0.1-0.2 |

### 模型训练相关参数

| 参数 | 含义 | 常用值 |
|------|------|--------|
| `model_type` | 模型类型 | `lr`, `xgb`, `lgbm`, `mlp`, `svm`, `rdf` |
| `n_estimators` | 树模型迭代次数 | 100-500 |
| `learning_rate` | 学习率 | 0.01-0.3 |
| `max_depth` | 树最大深度 | 3-8 |

---

## 输出文件位置

所有输出文件都在 `/workspace/` 目录下：

```
/workspace/
├── bins_result/              # 分箱报告
│   ├── bins_rpt_*.xlsx       # WOE/IV报告
│   └── *.png                 # 分箱图表
├── feature_selection/        # 特征选择
│   ├── selected_features.json
│   └── corr_matrix.xlsx      # 相关性矩阵
├── feature_encoding/         # 特征编码
│   └── *_encode_data.csv     # 编码后数据
├── binary_model/             # 二分类模型
│   ├── *_model.pkl           # 模型文件
│   ├── *_full_report.xlsx    # 完整评估报告
│   └── *.png                 # KS/AUC/LIFT曲线
├── pca_analysis/             # PCA 分析
│   └── pca_data.csv          # 降维数据
├── kmeans_clustering/        # 聚类分析
│   └── kmeans_result.csv     # 聚类结果
└── desc_stats/               # 描述统计
    ├── desc_num_rpt.xlsx     # 数值型特征统计
    └── desc_cat_rpt.xlsx     # 分类型特征统计
```

---

## 快捷命令

### 启动服务
```bash
cd /media/chenbh17/cbhssd/python-mcp-notebook-Copy1
python mcp_server.py
```

### 安装依赖
```python
install_package_tool(package='pandas')
install_package_tool(package='scikit-learn')
install_package_tool(package='lightgbm')
install_package_tool(package='xgboost')
```

### 查看文件
```python
list_files_tool(path="")  # 查看根目录
list_files_tool(path="binary_model")  # 查看模型目录
```

### 获取下载链接
```python
get_download_link_tool(filepath="binary_model/lgbm_full_report.xlsx")
```

---

## 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 工具调用失败 | 文件路径错误 | 检查路径是否相对于 `/workspace` |
| 模型训练报错 | 数据格式不对 | 确保目标变量为 0/1 格式 |
| 数据库连接失败 | 配置错误 | 检查 host/port/user/password |
| 内存不足 | 数据量太大 | 减少数据量或增加容器内存 |
| 文件找不到 | 路径前缀问题 | 移除路径前的 `/workspace/` 前缀 |

---

## 性能提示

1. **大数据集处理**: 使用 `execute_code_tool` 分块处理
2. **并行计算**: 在 `execute_code_tool` 中使用 `joblib.Parallel`
3. **缓存中间结果**: 将分箱映射、WOE 字典等保存为 pickle 文件
4. **增量建模**: 先在小样本上测试，再全量训练

---

## 联系与支持

- 详细文档：`CBHPACKS_MCP_TOOL_GUIDE.md`
- 完整清单：`MCP_TOOLS_COMPLETE_LIST.md`
- 集成总结：`CBHPACKS_INTEGRATION_SUMMARY.md`
