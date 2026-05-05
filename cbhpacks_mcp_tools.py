"""
cbhpacks MCP Tools - 将 cbhpacks 中的功能封装为 MCP 工具
包含数据预处理、特征工程、模型训练、数据库连接等功能
"""

import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
from mcp.server.fastmcp import FastMCP
from cbhpacks.models_for_try import get_random_data
from cbhpacks.bins_model import get_bins, bins_model
from cbhpacks.model_training import binary_model, uns_model, linear_model
from cbhpacks.cols_select import cols_select, cols_select_js
from cbhpacks.cols_encode import cols_encode
from cbhpacks.preprocess import cols_operate, desc_df, desc_col
from cbhpacks.con_linux import con_linux, data_trans_linux, jps, hadoop, start_hive
from cbhpacks.con_sql import chrun, chdf, con_mysql, con_hive, get_create_table, to_hive, rfms_sql

# 创建 MCP 实例
mcp = FastMCP("cbhpacks-mcp-server")

# 工作目录
WORKSPACE_DIR = "/workspace"

# ============================================
# 数据生成工具
# ============================================

@mcp.tool()
def generate_random_data(min_edge: int, max_edge: int, num: int, mth_cnt: int) -> dict:
    """
    生成随机测试数据表
    
    Args:
        min_edge: 随机整数最小值
        max_edge: 随机整数最大值
        num: 数据行数
        mth_cnt: 月份数量
    
    Returns:
        生成的数据表信息，包含列名、行数、数据预览等
    """
    try:
        data = get_random_data(min_edge, max_edge, num, mth_cnt)
        
        # 保存数据到 CSV
        output_path = os.path.join(WORKSPACE_DIR, f"random_data_{num}rows.csv")
        data.to_csv(output_path, index=False)
        
        return {
            "success": True,
            "message": f"成功生成{num}行随机数据",
            "columns": list(data.columns),
            "row_count": len(data),
            "file_path": output_path,
            "preview": data.head(5).to_dict('records')
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# 数据分箱工具
# ============================================

@mcp.tool()
def create_bins_report(
    data_file_path: str,
    cols: list,
    target: str,
    group: int = 10,
    nan_value: float = -9999,
    bins_type: str = 'eq_cnt',
    adj_bin: bool = False,
    cat_cols: list = None,
    output_dir: str = "bins_result"
) -> dict:
    """
    生成分箱报告（WOE、IV、KS 等）
    
    Args:
        data_file_path: 输入数据文件路径 (CSV 格式)
        cols: 需要分箱的特征列名列表
        target: 目标变量列名
        group: 分箱数量
        nan_value: 缺失值填充值
        bins_type: 分箱类型 (eq_cnt, eq_distance, deci_tree_bin, chi2_bin, cat_bin)
        adj_bin: 是否调整分箱
        cat_cols: 离散型特征列名列表，指定后这些列将使用 cat_bin 方式分箱；默认 None 表示全部按数值型处理
        output_dir: 输出目录名
    
    Returns:
        分箱结果信息
    """
    try:
        # 读取数据
        df = pd.read_csv(data_file_path)
        
        # 创建输出目录
        output_path = os.path.join(WORKSPACE_DIR, output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        # 创建分箱模型
        bm = bins_model(
            df=df,
            cols=cols,
            group=group,
            target=target,
            nan=nan_value,
            bins_type=bins_type,
            adj_bin=adj_bin,
            cat_cols=cat_cols if cat_cols else False,
            path=output_path
        )
        
        # 生成分箱报告
        woe_data, iv_data = bm.comp_woe_iv()
        
        # 保存结果
        woe_path = os.path.join(output_path, "woe_report.xlsx")
        iv_path = os.path.join(output_path, "iv_report.xlsx")
        woe_data.to_excel(woe_path, index=False)
        iv_data.to_excel(iv_path, index=False)
        
        return {
            "success": True,
            "message": "分箱报告生成成功",
            "woe_report_path": woe_path,
            "iv_report_path": iv_path,
            "iv_summary": iv_data.to_dict('records'),
            "output_directory": output_path
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def transform_to_woe(
    data_file_path: str,
    cols: list,
    target: str,
    group: int = 10,
    nan_value: float = -9999,
    bins_type: str = 'eq_cnt',
    adj_bin: bool = False,
    cat_cols: list = None,
    output_dir: str = "woe_transform"
) -> dict:
    """
    将数据转换为 WOE 编码
    
    Args:
        data_file_path: 输入数据文件路径
        cols: 需要转换的特征列名列表
        target: 目标变量列名
        group: 分箱数量
        nan_value: 缺失值填充值
        bins_type: 分箱类型
        adj_bin: 是否调整分箱
        cat_cols: 离散型特征列名列表，指定后这些列将使用 cat_bin 方式分箱；默认 None 表示全部按数值型处理
        output_dir: 输出目录名
    
    Returns:
        WOE 转换结果
    """
    try:
        df = pd.read_csv(data_file_path)
        
        output_path = os.path.join(WORKSPACE_DIR, output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        bm = bins_model(
            df=df,
            cols=cols,
            group=group,
            target=target,
            nan=nan_value,
            bins_type=bins_type,
            adj_bin=adj_bin,
            cat_cols=cat_cols if cat_cols else False,
            path=output_path
        )
        
        woe_df, woe_mapping = bm.data_to_woe()
        
        # 保存结果
        woe_data_path = os.path.join(output_path, "woe_data.csv")
        mapping_path = os.path.join(output_path, "woe_mapping.pkl")
        woe_df.to_csv(woe_data_path, index=False)
        
        import joblib
        joblib.dump(woe_mapping, mapping_path)
        
        return {
            "success": True,
            "message": "WOE 转换成功",
            "woe_data_path": woe_data_path,
            "mapping_path": mapping_path,
            "columns": list(woe_df.columns),
            "row_count": len(woe_df)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# 特征选择工具
# ============================================

@mcp.tool()
def feature_selection(
    data_file_path: str,
    cols: list,
    target: str,
    selection_methods: list = ['null', 'iv', 'corr'],
    iv_report_path: str = None,
    psi_report_path: str = None,
    null_pct: float = 0.95,
    enu_cnt: int = 1,
    enu_pct: float = 0.95,
    iv_thres: float = 0.01,
    corr_method: str = 'spearman',
    corr_thres: float = 0.8,
    psi_thres: float = 0.1,
    chi2_p_value_thres: float = 0.5,
    lg_method: str = 'recursion',
    lg_C: float = 0.1,
    ml_method: str = 'lgb',
    vif_thres: float = 10,
    nan_value: float = 0,
    output_dir: str = "feature_selection"
) -> dict:
    """
    特征选择工具，支持多种筛选方法
    
    Args:
        data_file_path: 输入数据文件路径
        cols: 候选特征列名列表
        target: 目标变量列名
        selection_methods: 筛选方法列表 (null, enumerate, iv, psi, corr, chi2, logistic, ml, vif)
        iv_report_path: IV 报告文件路径 (Excel 格式，由 create_bins_report 产出的 iv_report.xlsx)，使用 iv/corr 筛选方法时必填
        psi_report_path: PSI 平均报告文件路径 (Excel 格式，由 get_psi_report 产出的 psi_avg_rpt_*.xlsx)，使用 psi 筛选方法时必填
        null_pct: 缺失值阈值（缺失率超过此值的特征将被剔除）
        enu_cnt: 枚举值唯一数阈值（唯一值个数小于等于此值的特征将被剔除）
        enu_pct: 枚举值占比阈值（某一取值占比超过此值的特征将被剔除）
        iv_thres: IV 阈值（IV 值低于此阈值的特征将被剔除）
        corr_method: 相关系数计算方法 (spearman, pearson, kendall)
        corr_thres: 相关系数阈值（相关系数高于此值的特征对中剔除 IV 较低者）
        psi_thres: PSI 阈值（PSI 值高于此阈值的特征将被剔除）
        chi2_p_value_thres: 卡方检验 p 值阈值（p 值高于此阈值的特征将被剔除）
        lg_method: 逻辑回归筛选方式 (recursion 递归筛选, l1penalty L1正则化)
        lg_C: 逻辑回归正则化参数的倒数，值越小正则化越强
        ml_method: 机器学习筛选使用的模型 (lgb, xgb, rdf)
        vif_thres: VIF 方差膨胀因子阈值（VIF 高于此阈值的特征将被剔除）
        nan_value: 缺失值填充值
        output_dir: 输出目录名
    
    Returns:
        特征选择结果
    """
    try:
        df = pd.read_csv(data_file_path)
        
        output_path = os.path.join(WORKSPACE_DIR, output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        # 读取 IV 报告数据（iv/corr 方法需要）
        iv_data = None
        if iv_report_path:
            iv_data = pd.read_excel(iv_report_path)
        
        # 读取 PSI 报告数据（psi 方法需要）
        psi_data = None
        if psi_report_path:
            psi_data = pd.read_excel(psi_report_path)
        
        # 校验必要的数据依赖
        if ('iv' in selection_methods or 'corr' in selection_methods) and iv_data is None:
            return {"success": False, "error": "使用 iv 或 corr 筛选方法时，必须提供 iv_report_path 参数（由 create_bins_report 工具产出的 iv_report.xlsx）"}
        
        if 'psi' in selection_methods and psi_data is None:
            return {"success": False, "error": "使用 psi 筛选方法时，必须提供 psi_report_path 参数（由 get_psi_report 工具产出的 psi_avg_rpt_*.xlsx）"}
        
        cs = cols_select(
            df=df,
            cols=cols,
            target=target,
            iv_data=iv_data,
            psi_data=psi_data,
            null_pct=null_pct,
            enu_cnt=enu_cnt,
            enu_pct=enu_pct,
            iv_thres=iv_thres,
            corr_method=corr_method,
            corr_thres=corr_thres,
            psi_thres=psi_thres,
            chi2_p_value_thres=chi2_p_value_thres,
            lg_method=lg_method,
            lg_C=lg_C,
            ml_method=ml_method,
            vif_thres=vif_thres,
            nan=nan_value,
            path=output_path
        )
        
        selected_features = {}
        
        if 'null' in selection_methods:
            null_cols = cs.null_select()
            selected_features['null_selected'] = null_cols
        
        if 'enumerate' in selection_methods:
            enum_cols = cs.enumerate_select()
            selected_features['enumerate_selected'] = enum_cols
        
        if 'iv' in selection_methods:
            iv_cols = cs.iv_select()
            selected_features['iv_selected'] = iv_cols
        
        if 'psi' in selection_methods:
            psi_cols = cs.psi_select()
            selected_features['psi_selected'] = psi_cols
        
        if 'corr' in selection_methods:
            corr_stay, corr_data, corr_matrix = cs.corr_select()
            selected_features['corr_selected'] = corr_stay
            
            # 保存相关性矩阵
            corr_data.to_excel(os.path.join(output_path, "corr_detail.xlsx"), index=False)
        
        if 'chi2' in selection_methods:
            chi2_cols, chi2_df = cs.chi2_select()
            selected_features['chi2_selected'] = chi2_cols
        
        if 'logistic' in selection_methods:
            lg_cols = cs.logistic_select()
            selected_features['logistic_selected'] = lg_cols
        
        if 'ml' in selection_methods:
            ml_cols, ml_imp = cs.ml_select()
            selected_features['ml_selected'] = ml_cols
        
        if 'vif' in selection_methods:
            vif_cols, vif_detail = cs.vif_select()
            selected_features['vif_selected'] = vif_cols
        
        # 保存最终选择的特征
        final_cols = cs.cols_s
        with open(os.path.join(output_path, "selected_features.json"), 'w') as f:
            json.dump(final_cols, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "message": f"特征选择完成，从{len(cols)}个特征中筛选出{len(final_cols)}个特征",
            "selected_features": final_cols,
            "selection_details": {k: len(v) for k, v in selected_features.items()},
            "output_directory": output_path
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# 数据编码工具
# ============================================

@mcp.tool()
def encode_features(
    data_file_path: str,
    cols: list,
    encode_type: str = 'minmax',
    target: str = None,
    group: int = 10,
    nan_value: float = -9999,
    bins_type: str = 'eq_cnt',
    adj_bin: bool = False,
    output_dir: str = "feature_encoding"
) -> dict:
    """
    特征编码工具
    
    Args:
        data_file_path: 输入数据文件路径
        cols: 需要编码的特征列名列表
        encode_type: 编码类型 (minmax, sc, sigmoid, softmax, bins, count, woe)
        target: 目标变量 (WOE 编码时需要)
        group: 分箱数量 (分箱编码时需要)
        nan_value: 缺失值填充值
        bins_type: 分箱类型
        adj_bin: 是否调整分箱（分箱编码/WOE编码时使用）
        output_dir: 输出目录名
    
    Returns:
        编码结果
    """
    try:
        df = pd.read_csv(data_file_path)
        
        output_path = os.path.join(WORKSPACE_DIR, output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        ce = cols_encode(
            df=df,
            cols=cols,
            bins_type=bins_type,
            group=group,
            target=target if target else 'target',
            nan=nan_value,
            adj_bin=adj_bin,
            path=output_path
        )
        
        if encode_type == 'minmax':
            encoded_data = ce.data_to_minmax()
            output_file = "minmax_encode_data.csv"
        elif encode_type == 'sc':
            encoded_data = ce.data_to_sc()
            output_file = "sc_encode_data.csv"
        elif encode_type == 'sigmoid':
            encoded_data = ce.data_to_sigmoid()
            output_file = "sigmoid_encode_data.csv"
        elif encode_type == 'softmax':
            encoded_data = ce.data_to_softmax()
            output_file = "softmax_encode_data.csv"
        elif encode_type == 'bins':
            encoded_data, details = ce.bins_to_num()
            output_file = "bins_encode_data.csv"
        elif encode_type == 'count':
            encoded_data, details = ce.str_to_num()
            output_file = "count_encode_data.csv"
        elif encode_type == 'woe':
            if target is None:
                return {"success": False, "error": "WOE 编码需要指定 target 参数"}
            encoded_data, woe_dic = ce.data_to_woe()
            output_file = "woe_encode_data.csv"
        else:
            return {"success": False, "error": f"不支持的编码类型：{encode_type}"}
        
        output_file_path = os.path.join(output_path, output_file)
        encoded_data[cols].to_csv(output_file_path, index=False)
        
        return {
            "success": True,
            "message": f"{encode_type}编码完成",
            "output_file": output_file_path,
            "columns": list(encoded_data.columns),
            "row_count": len(encoded_data)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# 二分类模型训练工具
# ============================================

@mcp.tool()
def train_binary_model(
    train_data_path: str,
    test_data_path: str,
    cols: list,
    target: str,
    model_type: str = 'lgbm',
    model_params: dict = None,
    output_dir: str = "binary_model"
) -> dict:
    """
    训练二分类模型（支持 LR、XGBoost、LightGBM、MLP、SVM、随机森林）
    
    Args:
        train_data_path: 训练数据文件路径
        test_data_path: 测试数据文件路径
        cols: 特征列名列表
        target: 目标变量列名
        model_type: 模型类型 (lr, xgb, lgbm, mlp, svm, rdf)
        model_params: 模型参数字典
        output_dir: 输出目录名
    
    Returns:
        模型训练结果
    """
    try:
        train_df = pd.read_csv(train_data_path)
        test_df = pd.read_csv(test_data_path)
        
        output_path = os.path.join(WORKSPACE_DIR, output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        mt = binary_model(
            train=train_df,
            test=test_df,
            cols=cols,
            target=target,
            model_path=output_path,
            train_data_path=os.path.join(output_path, "datas")
        )
        
        # 训练模型
        if model_type == 'lr':
            params = model_params or {'penalty': 'l2', 'C': 1, 'solver': 'saga', 'max_iter': 100}
            mt.lr_fit(**params)
        elif model_type == 'xgb':
            params = model_params or {'n_estimators': 100}
            mt.xgb_fit(**params)
        elif model_type == 'lgbm':
            params = model_params or {
                'colsample_bytree': 0.35, 'learning_rate': 0.14, 'num_leaves': 13,
                'min_child_weight': 45, 'min_gain_to_split': 0.45,
                'reg_alpha': 2.2, 'reg_lambda': 2.2, 'max_depth': 5,
                'n_estimators': 110, 'metric': 'roc_auc'
            }
            mt.lgbm_fit(**params)
        elif model_type == 'mlp':
            params = model_params or {'epochs': 30, 'batch_size': 10}
            mt.mlp_fit(**params)
        elif model_type == 'svm':
            params = model_params or {'kernel': 'linear', 'probability': True}
            mt.svm_fit(**params)
        elif model_type == 'rdf':
            params = model_params or {}
            mt.rdf_fit(**params)
        else:
            return {"success": False, "error": f"不支持的模型类型：{model_type}"}
        
        # 保存模型配置信息（供 generate_model_report 使用）
        model_config = {
            'model_type': model_type,
            'cols': cols,
            'target': target
        }
        with open(os.path.join(output_path, "model_config.json"), 'w') as f:
            json.dump(model_config, f, indent=2, ensure_ascii=False)
        
        # 保存训练集和测试集数据（保留全部列，供 generate_model_report 按月份分箱等使用）
        datas_path = os.path.join(output_path, "datas")
        os.makedirs(datas_path, exist_ok=True)
        train_df.to_csv(os.path.join(datas_path, "train.csv"), index=False)
        test_df.to_csv(os.path.join(datas_path, "test.csv"), index=False)
        
        return {
            "success": True,
            "message": f"{model_type}模型训练完成",
            "model_type": model_type,
            "model_path": output_path,
            "train_rows": len(train_df),
            "test_rows": len(test_df),
            "features_count": len(cols)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def generate_model_report(
    model_path: str,
    group: int = 30,
    bins_type: str = 'all',
    mth_col: str = None,
    base_mth: int = None
) -> dict:
    """
    生成模型评估报告（混淆矩阵、KS、AUC、LIFT 等）
    
    Args:
        model_path: 模型所在目录路径
        group: 评分分箱数量
        bins_type: 分箱类型 (all, eq_cnt, eq_distance)
        mth_col: 月份列名
        base_mth: 基准月份
    
    Returns:
        模型报告生成结果
    """
    try:
        # 加载模型配置
        config_path = os.path.join(model_path, "model_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            return {"success": False, "error": "未找到模型配置文件 model_config.json，请先使用 train_binary_model 训练模型"}
        
        model_type = config['model_type']
        
        # 加载模型对象
        import joblib
        model_file = os.path.join(model_path, f"{model_type}_model.pkl")
        if not os.path.exists(model_file):
            return {"success": False, "error": f"未找到模型文件 {model_type}_model.pkl"}
        model = joblib.load(model_file)
        
        # 加载训练集和测试集
        train_path = os.path.join(model_path, "datas", "train.csv")
        test_path = os.path.join(model_path, "datas", "test.csv")
        if not os.path.exists(train_path) or not os.path.exists(test_path):
            return {"success": False, "error": "未找到训练集/测试集数据 (datas/train.csv, datas/test.csv)，请先使用 train_binary_model 训练模型"}
        
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
        
        mt = binary_model(
            train=train_df,
            test=test_df,
            cols=config['cols'],
            target=config['target'],
            model_path=model_path,
            train_data_path=os.path.join(model_path, "datas")
        )
        mt.clf = model
        mt.model_type = model_type
        
        # 从训练产出的重要性/系数文件中恢复 cols_weight 属性
        imp_file_map = {
            'lgbm': ('lgbm_imp.xlsx', 'excel'),
            'xgb': ('xgb_imp.xlsx', 'excel'),
            'lr': ('lr_coef.xlsx', 'excel'),
            'svm': ('svm_imp.xlsx', 'excel'),
            'rdf': ('rdf_imp.xlsx', 'excel'),
            'keras': ('mlp_weight.csv', 'csv'),
        }
        if model_type in imp_file_map:
            imp_filename, imp_format = imp_file_map[model_type]
            imp_path = os.path.join(model_path, imp_filename)
            if os.path.exists(imp_path):
                if imp_format == 'excel':
                    mt.cols_weight = pd.read_excel(imp_path)
                else:
                    mt.cols_weight = pd.read_csv(imp_path)
            else:
                return {"success": False, "error": f"未找到特征重要性/系数文件 {imp_filename}，无法生成报告"}
        else:
            return {"success": False, "error": f"不支持的模型类型：{model_type}"}
        
        bins_rpt, confusion_matrix, fea_bins_report, fea_report = mt.report(
            group=group,
            mth_col=mth_col if mth_col else 'mth',
            base_mth=base_mth if base_mth else 202401,
            bins_type=bins_type
        )
        
        return {
            "success": True,
            "message": "模型报告生成成功",
            "report_files": [
                os.path.join(model_path, f"{model_type}_{group}bins_full_report.xlsx"),
                os.path.join(model_path, f"confusion_matrix_{model_type}_noadj.xlsx"),
            ],
            "auc_test": float(confusion_matrix[confusion_matrix['type']=='test']['auc'].values[0]),
            "ks_test": float(confusion_matrix[confusion_matrix['type']=='test']['ks'].values[0])
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# 无监督学习工具
# ============================================

@mcp.tool()
def pca_analysis(
    data_file_path: str,
    cols: list,
    mean_key: list,
    target: str,
    var_ratio_cumsum: float = 0.8,
    output_dir: str = "pca_analysis"
) -> dict:
    """
    主成分分析 (PCA)
    
    Args:
        data_file_path: 输入数据文件路径
        cols: 特征列名列表
        mean_key: 主键列名列表
        target: 目标变量列名
        var_ratio_cumsum: 累计方差解释比例阈值
        output_dir: 输出目录名
    
    Returns:
        PCA 分析结果
    """
    try:
        df = pd.read_csv(data_file_path)
        
        output_path = os.path.join(WORKSPACE_DIR, output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        um = uns_model(
            df=df.fillna(0),
            cols=cols,
            target=target,
            mean_key=mean_key,
            path=output_path
        )
        
        pca_cols, pca_data, pca_detail = um.pca(var_ratio_cumsum=var_ratio_cumsum)
        
        return {
            "success": True,
            "message": "PCA 分析完成",
            "pca_components": pca_cols,
            "components_count": len(pca_cols),
            "pca_data_path": os.path.join(output_path, "pca_data.csv"),
            "pca_details_path": os.path.join(output_path, "pca_details.csv"),
            "variance_explained": var_ratio_cumsum
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def kmeans_clustering(
    data_file_path: str,
    cols: list,
    n_clusters: int = 10,
    output_dir: str = "kmeans_clustering"
) -> dict:
    """
    K-Means 聚类分析
    
    Args:
        data_file_path: 输入数据文件路径
        cols: 特征列名列表
        n_clusters: 聚类个数
        output_dir: 输出目录名
    
    Returns:
        聚类结果
    """
    try:
        df = pd.read_csv(data_file_path)
        
        output_path = os.path.join(WORKSPACE_DIR, output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        um = uns_model(
            df=df.fillna(0),
            cols=cols,
            target=None,
            path=output_path
        )
        
        data, kmeans_detail = um.kmeans(n_clusters=n_clusters)
        
        # 保存结果
        result_path = os.path.join(output_path, "kmeans_result.csv")
        data.to_csv(result_path, index=False)
        
        return {
            "success": True,
            "message": f"K-Means 聚类完成，共{n_clusters}个簇",
            "cluster_labels_path": os.path.join(output_path, "cluster_labels.pkl"),
            "cluster_centers_path": os.path.join(output_path, "kmeans_center.xlsx"),
            "result_path": result_path,
            "data_rows": len(data)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# 线性回归工具
# ============================================

@mcp.tool()
def linear_regression(
    data_file_path: str,
    cols: list,
    target: str,
    iv_target: str = None,
    iv_col: str = None,
    output_dir: str = "linear_model"
) -> dict:
    """
    线性回归分析（OLS、Logit、工具变量回归）
    
    Args:
        data_file_path: 输入数据文件路径
        cols: 解释变量列名列表
        target: 被解释变量列名
        iv_target: 工具变量回归的目标列
        iv_col: 工具变量列
        output_dir: 输出目录名
    
    Returns:
        回归分析结果
    """
    try:
        df = pd.read_csv(data_file_path)
        
        output_path = os.path.join(WORKSPACE_DIR, output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        lm = linear_model(
            df=df,
            cols=cols,
            iv_target=iv_target if iv_target else cols[0],
            iv_col=iv_col if iv_col else cols[-1],
            target=target,
            path=output_path
        )
        
        # OLS 回归
        model = lm.ols()
        
        result = {
            "success": True,
            "message": "线性回归分析完成",
            "model_type": lm.model_name,
            "output_directory": output_path,
            "summary_files": [
                os.path.join(output_path, f"{lm.model_name}_Significance_summary.xlsx")
            ]
        }
        
        # 如果指定了工具变量，执行 IV 回归
        if iv_target and iv_col:
            ols1, ols2 = lm.IV()
            result['iv_result'] = "工具变量回归完成"
        
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# 数据描述统计工具
# ============================================

@mcp.tool()
def descriptive_statistics(
    data_file_path: str,
    cols: list = None,
    cat_cols: list = [],
    output_dir: str = "desc_stats"
) -> dict:
    """
    描述性统计分析
    
    Args:
        data_file_path: 输入数据文件路径
        cols: 需要分析的特征列表（可选，默认分析所有列）
        cat_cols: 离散型特征列表
        output_dir: 输出目录名
    
    Returns:
        描述统计结果
    """
    try:
        df = pd.read_csv(data_file_path)
        
        if cols is None:
            cols = list(df.columns)
        
        output_path = os.path.join(WORKSPACE_DIR, output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        desc = desc_df(
            df=df,
            cols=cols,
            cat_cols=cat_cols,
            path=output_path
        )
        
        num_report, cat_report = desc.get_rpt()
        
        return {
            "success": True,
            "message": "描述性统计分析完成",
            "numeric_features_count": len(num_report),
            "categorical_features_count": len(cat_report),
            "num_report_path": os.path.join(output_path, "desc_num_rpt.xlsx"),
            "cat_report_path": os.path.join(output_path, "desc_cat_rpt.xlsx"),
            "numeric_summary": num_report.head(10).to_dict('records'),
            "categorical_summary": cat_report.head(10).to_dict('records')
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# 数据库查询工具
# ============================================

@mcp.tool()
def query_clickhouse(sql: str) -> dict:
    """
    ClickHouse 数据库查询
    
    Args:
        sql: SQL 查询语句（可包含多条，用分号分隔）
    
    Returns:
        查询结果
    """
    try:
        result = chdf(sql)
        
        if isinstance(result, list):
            return {
                "success": True,
                "message": f"ClickHouse 查询完成，返回{len(result)}个结果集",
                "results_count": len(result),
                "first_result_preview": result[0].head(5).to_dict('records') if len(result) > 0 else []
            }
        else:
            return {
                "success": True,
                "message": "ClickHouse 查询完成",
                "rows": len(result),
                "columns": list(result.columns),
                "preview": result.head(5).to_dict('records')
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def execute_clickhouse(sql: str) -> dict:
    """
    ClickHouse 执行 SQL（INSERT、CREATE 等）
    
    Args:
        sql: SQL 执行语句
    
    Returns:
        执行结果
    """
    try:
        result = chrun(sql)
        return {"success": True, "message": "ClickHouse SQL 执行成功", "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def query_mysql(
    sql: str,
    host: str = '192.168.10.200',
    port: int = 3306,
    user: str = 'hive',
    password: str = 'hive',
    database: str = 'dev',
    charset: str = None
) -> dict:
    """
    MySQL 数据库查询
    
    Args:
        sql: SQL 查询语句
        host: MySQL 服务器地址
        port: MySQL 端口
        user: 用户名
        password: 密码
        database: 数据库名
        charset: 字符编码（如 utf8、gbk 等），默认 None
    
    Returns:
        查询结果
    """
    try:
        result = con_mysql(sql=sql, host=host, port=port, user=user, password=password, database=database, charset=charset)
        
        if isinstance(result, list):
            return {
                "success": True,
                "message": f"MySQL 查询完成，返回{len(result)}个结果集",
                "results_count": len(result)
            }
        elif result is not None:
            return {
                "success": True,
                "message": "MySQL 查询完成",
                "rows": len(result),
                "columns": list(result.columns),
                "preview": result.head(5).to_dict('records')
            }
        else:
            return {"success": True, "message": "SQL 执行成功，无返回结果"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def query_hive(
    sql: str,
    host: str = '192.168.10.100',
    port: int = 10000,
    auth: str = 'CUSTOM',
    username: str = 'hive',
    password: str = 'hive',
    database: str = 'pro'
) -> dict:
    """
    Hive 数据库查询
    
    Args:
        sql: SQL 查询语句
        host: Hive 服务器地址
        port: Hive 端口
        auth: 认证方式（默认 CUSTOM）
        username: 用户名
        password: 密码
        database: 数据库名
    
    Returns:
        查询结果
    """
    try:
        result = con_hive(sql=sql, host=host, port=port, auth=auth, username=username, password=password, database=database)
        
        if isinstance(result, list):
            return {
                "success": True,
                "message": f"Hive 查询完成，返回{len(result)}个结果集",
                "results_count": len(result)
            }
        elif result is not None:
            return {
                "success": True,
                "message": "Hive 查询完成",
                "rows": len(result),
                "columns": list(result.columns),
                "preview": result.head(5).to_dict('records')
            }
        else:
            return {"success": True, "message": "SQL 执行成功，无返回结果"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def save_to_hive(
    data_file_path: str,
    table_name: str,
    local_loc: str,
    method: str = 'overwrite',
    encoding: str = 'UTF-8',
    partition: bool = False,
    partition_col: str = 'year string',
    bucket: bool = False,
    bucket_col: str = None,
    bucket_num: int = 10,
    shell_loc: str = '/media/chenbh17/cbhssd/invest/data/'
) -> dict:
    """
    将数据保存到 Hive 表
    
    Args:
        data_file_path: 本地数据文件路径
        table_name: Hive 表名（需包含库名）
        local_loc: 本地文件保存路径
        method: 写入方式 (overwrite, append)
        encoding: 文件编码
        partition: 是否分区
        partition_col: 分区列（格式: '列名 类型'，如 'year string'）
        bucket: 是否分桶
        bucket_col: 分桶列名
        bucket_num: 分桶数量
        shell_loc: Linux 服务器上的临时文件存放路径
    
    Returns:
        保存结果
    """
    try:
        df = pd.read_csv(data_file_path)
        
        result = to_hive(
            data=df,
            table_name=table_name,
            local_loc=local_loc,
            shell_loc=shell_loc,
            method=method,
            encoding=encoding,
            partition=partition,
            bucket=bucket,
            partition_col=partition_col,
            bucket_col=bucket_col,
            bucket_num=bucket_num
        )
        
        return {"success": True, "message": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# Linux 命令执行工具
# ============================================

@mcp.tool()
def execute_linux_command(shell: str, user: str = 'chenbh17') -> dict:
    """
    在 Linux 服务器上执行 Shell 命令
    
    Args:
        shell: Shell 命令（可包含多条，用分号分隔）
        user: 登录用户 (chenbh17 或 root)
    
    Returns:
        命令执行结果
    """
    try:
        # 注意：实际执行需要配置 SSH 连接信息
        result = con_linux(shell, user)
        return {"success": True, "message": "命令执行完成", "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# 文件上传工具
# ============================================

@mcp.tool()
def upload_file(
    container_file_path: str
) -> dict:
    """
    获取文件上传 URL 和说明
    
    使用说明：
    此工具返回上传 URL，客户端需要通过 HTTP POST 上传文件到容器
    
    Args:
        container_file_path: 容器中目标文件路径（相对于/workspace 目录，如：data/train.csv）
    
    Returns:
        上传指南，包含：
        - upload_url: 上传文件的 HTTP POST 地址
        - instructions: 详细的上传方法说明
    
    客户端上传方法（3 种方式任选其一）：
    
    **方法 1: 使用 requests 库（推荐）**
    ```python
    import requests
    
    # 调用工具获取上传 URL
    result = client.call_tool('upload_file', {
        'container_file_path': 'data/train.csv'
    })
    
    if result['success']:
        upload_url = result['upload_url']
        
        # 上传文件
        with open('local_file.csv', 'rb') as f:
            files = {'file': f}
            data = {'filepath': 'data/train.csv'}
            response = requests.post(upload_url, files=files, data=data)
        
        print(response.json())
    ```
    
    **方法 2: 使用 curl 命令**
    ```bash
    curl -X POST http://{external-host}/{container_id}/upload \\
      -F "file=@local_file.csv" \\
      -F "filepath=data/train.csv"
    ```
    
    **方法 3: 从 URL 下载文件到容器**
    ```python
    import requests
    
    upload_url = "http://{external-host}/{container_id}/upload"
    filepath = "data/train.csv"
    file_url = "https://example.com/data.csv"  # 文件的 HTTP URL
    
    response = requests.post(upload_url, json={
        'filepath': filepath,
        'file_url': file_url
    })
    ```
    
    注意：
    - 文本文件和二进制文件都支持
    - 文件大小建议不超过 100MB
    - 超大文件建议分块上传或使用 URL 方式
    """
    try:
        import socket
        
        # 获取容器 ID
        hostname = socket.gethostname()
        container_id = hostname if len(hostname) == 12 and all(c in '0123456789abcdef' for c in hostname.lower()) else 'unknown'
        
        # 获取外部主机名和端口配置
        external_host = os.environ.get('EXTERNAL_HOST', 'localhost')
        include_port = os.environ.get('INCLUDE_PORT', 'false').lower() == 'true'
        
        # 判断是否为 IP 地址格式
        import re
        is_ip_address = re.match(r'^\\d+\\.\\d+\\.\\d+\\.\\d+$', external_host) is not None
        
        # 对于域名，默认不包含端口；对于 IP 地址，默认包含端口
        if is_ip_address:
            include_port = os.environ.get('INCLUDE_PORT', 'true').lower() == 'true'
        else:
            include_port = os.environ.get('INCLUDE_PORT', 'false').lower() == 'true'
        
        # 构建基础 URL
        if include_port:
            base_url = f"http://{external_host}:70"
        else:
            base_url = f"http://{external_host}"
        
        # 构建上传 URL
        upload_url = f"{base_url}/{container_id}/upload"
        
        return {
            "success": True,
            "message": "请通过 HTTP POST 上传文件",
            "upload_url": upload_url,
            "container_file_path": container_file_path,
            "container_id": container_id,
            "instructions": {
                "method1_requests": "使用 Python requests 库上传（见 docstring 示例）",
                "method2_curl": "使用 curl 命令上传（见 docstring 示例）",
                "method3_url": "提供文件的 HTTP URL，容器自动下载"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def download_file(
    container_file_path: str
) -> dict:
    """
    获取文件下载 URL
    
    使用说明：
    此工具返回文件的 HTTP 下载 URL，客户端通过 HTTP GET 下载文件
    
    Args:
        container_file_path: 容器中的文件路径（相对于/workspace 目录，如：data/result.csv）
    
    Returns:
        下载结果，包含：
        - success: 是否成功
        - download_url: 下载文件的完整 HTTP URL
        - file_exists: 文件是否存在
        - file_size: 文件大小（字节）
        - filename: 文件名
    
    客户端下载方法（3 种方式任选其一）：
    
    **方法 1: 使用 requests 库（推荐）**
    ```python
    import requests
    
    # 调用工具获取下载 URL
    result = client.call_tool('download_file', {
        'container_file_path': 'output/result.csv'
    })
    
    if result['success']:
        download_url = result['download_url']
        
        # 下载文件
        response = requests.get(download_url)
        with open('local_result.csv', 'wb') as f:
            f.write(response.content)
        print(f"文件已保存到 local_result.csv")
    ```
    
    **方法 2: 使用 wget 命令**
    ```bash
    wget http://{external-host}/{container_id}/download/output/result.csv -O local_result.csv
    ```
    
    **方法 3: 直接在浏览器打开**
    将 download_url 在浏览器中打开即可下载文件
    
    注意：
    - 确保容器正在运行
    - 确保文件路径正确（相对于 /workspace 目录）
    - 下载 URL 有效期与容器运行时间相同
    """
    try:
        import socket
        
        # 检查文件是否存在
        source_path = os.path.join(WORKSPACE_DIR, container_file_path.lstrip('/'))
        file_exists = os.path.exists(source_path) and os.path.isfile(source_path)
        
        if not file_exists:
            return {
                "success": False,
                "error": f"文件不存在：{source_path}",
                "file_exists": False
            }
        
        file_size = os.path.getsize(source_path)
        filename = os.path.basename(source_path)
        
        # 获取容器 ID
        hostname = socket.gethostname()
        container_id = hostname if len(hostname) == 12 and all(c in '0123456789abcdef' for c in hostname.lower()) else 'unknown'
        
        # 获取外部主机名和端口配置
        external_host = os.environ.get('EXTERNAL_HOST', 'localhost')
        include_port = os.environ.get('INCLUDE_PORT', 'false').lower() == 'true'
        
        # 判断是否为 IP 地址格式
        import re
        is_ip_address = re.match(r'^\\d+\\.\\d+\\.\\d+\\.\\d+$', external_host) is not None
        
        # 对于域名，默认不包含端口；对于 IP 地址，默认包含端口
        if is_ip_address:
            include_port = os.environ.get('INCLUDE_PORT', 'true').lower() == 'true'
        else:
            include_port = os.environ.get('INCLUDE_PORT', 'false').lower() == 'true'
        
        # 构建基础 URL
        if include_port:
            base_url = f"http://{external_host}:70"
        else:
            base_url = f"http://{external_host}"
        
        # 构建下载 URL
        download_url = f"{base_url}/{container_id}/download/{container_file_path.lstrip('/')}"
        
        return {
            "success": True,
            "message": "文件存在，可通过以下 URL 下载",
            "download_url": download_url,
            "file_exists": True,
            "file_size": f"{file_size} bytes",
            "filename": filename,
            "container_file_path": container_file_path,
            "instructions": {
                "method1_requests": "使用 Python requests 库下载（见 docstring 示例）",
                "method2_wget": "使用 wget 命令下载（见 docstring 示例）",
                "method3_browser": "直接在浏览器打开 download_url"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# 补充工具 - 单变量分析、RFMS 特征衍生等
# ============================================

@mcp.tool()
def single_column_analysis(
    data_file_path: str,
    col: str,
    cols: list,
    target: str,
    cat_cols: list = [],
    corr_threshold: float = 0.5,
    output_dir: str = "single_col_analysis"
) -> dict:
    """
    单变量详细描述分析（描述性、相关性、有监督、异常值检测）
    
    Args:
        data_file_path: 输入数据文件路径
        col: 要分析的单个特征列名
        cols: 数据集中的所有特征列表
        target: 目标变量列名
        cat_cols: 离散型特征列表
        corr_threshold: 相关性阈值
        output_dir: 输出目录名
    
    Returns:
        单变量分析结果
    """
    try:
        df = pd.read_csv(data_file_path)
        
        output_path = os.path.join(WORKSPACE_DIR, output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        dc = desc_col(
            df=df,
            cols=cols,
            target=target,
            col=col,
            cat_cols=cat_cols,
            corr_threshold=corr_threshold,
            path=output_path
        )
        
        # 执行完整分析卡片
        dc.feat_card()
        
        return {
            "success": True,
            "message": f"单变量{col}分析完成",
            "output_directory": output_path,
            "report_files": [
                os.path.join(output_path, f"{col}_desc.xlsx"),
                os.path.join(output_path, f"{col}_corr.xlsx"),
                os.path.join(output_path, f"{col}_woe.xlsx"),
                os.path.join(output_path, f"{col}_outlier.png"),
                os.path.join(output_path, f"{col}_distribution.png")
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def rfms_feature_engineering(
    data_file_path: str,
    cols: list,
    origin_table: str,
    new_table: str,
    day_list: list = None
) -> dict:
    """
    RFMS 范式特征衍生（滚动窗口统计特征）
    
    Args:
        data_file_path: 输入数据文件路径（用于获取数据结构）
        cols: 需要衍生的特征列名列表
        origin_table: 原始 Hive 表名
        new_table: 新生成的 Hive 表名
        day_list: 时间窗口列表（默认 [5, 20, 120, 250]）
    
    Returns:
        特征衍生结果
    """
    try:
        df = pd.read_csv(data_file_path)
        
        if day_list is None:
            day_list = [5, 20, 120, 250]
        
        result = rfms_sql(
            data=df,
            cols=cols,
            new_table=new_table,
            origin_table=origin_table,
            day_list=day_list
        )
        
        return {
            "success": True,
            "message": result,
            "new_table": new_table,
            "derived_features_count": len(cols) * len(day_list) * 5  # sum, avg, stddev, min, max
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def bootstrap_feature_selection(
    data_file_path: str,
    cols: list,
    target: str,
    num_iterations: int = 10,
    frac: float = 1.0,
    boot_thres: float = 1000,
    boot_method: str = 'lgb',
    output_dir: str = "bootstrap_selection"
) -> dict:
    """
    Bootstrap 特征选择（有放回抽样评估特征重要性）
    
    Args:
        data_file_path: 输入数据文件路径
        cols: 候选特征列名列表
        target: 目标变量列名
        num_iterations: Bootstrap 迭代次数
        frac: 随机抽样比例
        boot_thres: 重要性阈值
        boot_method: 模型方法 (lgb, xgb, rdf)
        output_dir: 输出目录名
    
    Returns:
        Bootstrap 特征选择结果
    """
    try:
        df = pd.read_csv(data_file_path)
        
        output_path = os.path.join(WORKSPACE_DIR, output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        cs = cols_select(
            df=df,
            cols=cols,
            target=target,
            boot_method=boot_method,
            boot_thres=boot_thres,
            path=output_path
        )
        
        selected_cols, imp_data = cs.boostrap_select(
            num_iterations=num_iterations,
            frac=frac
        )
        
        return {
            "success": True,
            "message": f"Bootstrap 特征选择完成，从{len(cols)}个特征中筛选出{len(selected_cols)}个特征",
            "selected_features": selected_cols,
            "importance_data_path": os.path.join(output_path, "boot_select_imp_data.xlsx"),
            "iterations": num_iterations
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def recursive_feature_selection(
    train_data_path: str,
    test_data_path: str,
    cols: list,
    target: str,
    method: str = 'xgb',
    recursion_num: int = 30,
    stay_pct: float = 0.95,
    output_dir: str = "recursive_selection"
) -> dict:
    """
    递归特征选择（迭代筛选特征）
    
    Args:
        train_data_path: 训练数据文件路径
        test_data_path: 测试数据文件路径
        cols: 候选特征列名列表
        target: 目标变量列名
        method: 模型方法 (xgb, lgb)
        recursion_num: 递归迭代次数
        stay_pct: 每次迭代保留比例
        output_dir: 输出目录名
    
    Returns:
        递归特征选择结果
    """
    try:
        train_df = pd.read_csv(train_data_path)
        test_df = pd.read_csv(test_data_path)
        
        output_path = os.path.join(WORKSPACE_DIR, output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        js = cols_select_js(
            train=train_df,
            test=test_df,
            cols=cols,
            target=target,
            method=method,
            recursion_num=recursion_num,
            stay_pct=stay_pct,
            path=output_path
        )
        
        js_data, cols_detail, js_cols = js.recursion_select()
        
        return {
            "success": True,
            "message": f"递归特征选择完成，最终选择{len(js_cols)}个特征",
            "selected_features": js_cols,
            "iteration_data_path": os.path.join(output_path, f"js_recu_data_{method}.xlsx"),
            "best_iteration": len(js_cols)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_psi_report(
    data_file_path: str,
    cols: list,
    mth_col: str,
    base_mth: int,
    cmp_mth: int,
    bins_type: str = 'eq_cnt',
    group: int = 10,
    target: str = 'target',
    nan_value: float = -9999,
    adj_bin: bool = False,
    cat_cols: list = None,
    output_dir: str = "psi_report"
) -> dict:
    """
    计算 PSI（群体稳定性指标）报告
    
    Args:
        data_file_path: 输入数据文件路径
        cols: 特征列名列表
        mth_col: 月份列名
        base_mth: 基准月份
        cmp_mth: 比较月份
        bins_type: 分箱类型
        group: 分箱数量
        target: 目标变量列名
        nan_value: 缺失值填充值
        adj_bin: 是否调整分箱
        cat_cols: 离散型特征列名列表，指定后这些列将使用 cat_bin 方式分箱；默认 None 表示全部按数值型处理
        output_dir: 输出目录名
    
    Returns:
        PSI 报告结果
    """
    try:
        df = pd.read_csv(data_file_path)
        
        output_path = os.path.join(WORKSPACE_DIR, output_dir)
        os.makedirs(output_path, exist_ok=True)
        
        bm = bins_model(
            df=df,
            cols=cols,
            group=group,
            target=target,
            nan=nan_value,
            bins_type=bins_type,
            mth_col=mth_col,
            base_mth=base_mth,
            cmp_mth=cmp_mth,
            adj_bin=adj_bin,
            cat_cols=cat_cols if cat_cols else False,
            path=output_path
        )
        
        psi_data = bm.get_psi()
        psi_avg_data = bm.psi_mth_avg()
        
        return {
            "success": True,
            "message": "PSI 报告生成成功",
            "psi_single_path": os.path.join(output_path, f"psi_single_rpt_{bins_type}{base_mth}_{cmp_mth}.xlsx"),
            "psi_avg_path": os.path.join(output_path, f"psi_avg_rpt_{bins_type}.xlsx"),
            "psi_summary": psi_avg_data.to_dict('records')
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def create_hive_table(
    data_file_path: str,
    table_name: str,
    partition: bool = False,
    bucket: bool = False,
    partition_col: str = None,
    bucket_col: str = None,
    bucket_num: int = 10,
    encoding: str = None
) -> dict:
    """
    生成 Hive 建表语句
    
    Args:
        data_file_path: 数据文件路径（用于获取数据结构）
        table_name: Hive 表名（需包含库名）
        partition: 是否分区
        bucket: 是否分桶
        partition_col: 分区列
        bucket_col: 分桶列
        bucket_num: 分桶数量
        encoding: 编码格式
    
    Returns:
        建表语句
    """
    try:
        df = pd.read_csv(data_file_path)
        
        create_sql = get_create_table(
            data=df,
            table_name=table_name,
            encoding=encoding,
            partition=partition,
            bucket=bucket,
            partition_col=partition_col,
            bucket_col=bucket_col,
            bucket_num=bucket_num
        )
        
        return {
            "success": True,
            "message": "Hive 建表语句生成成功",
            "create_sql": create_sql,
            "columns": list(df.columns),
            "column_types": {col: str(df[col].dtype) for col in df.columns}
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# 主程序入口
# ============================================

if __name__ == "__main__":
    # 启动 MCP 服务
    print("Starting cbhpacks MCP server...")
    mcp.run()
