"""
练习 0-1：手算 Self-Attention
Q, K, V 是 3 个词，每词 2 维向量
"""
import numpy as np

# ========== 给定的数据 ==========
Q = np.array([[1, 0],   # q1
              [0, 1],   # q2
              [1, 1]])  # q3

K = np.array([[1, 1],   # k1
              [0, 1],   # k2
              [1, 0]])  # k3

V = np.array([[2, 0],   # v1
              [1, 1],   # v2
              [0, 2]])  # v3

# ========== ① 算 Attention 分数矩阵 ==========
# S[i][j] = Q[i] · K[j]  即矩阵乘法 Q @ K^T
S = Q @ K.T
print("① Attention 分数矩阵 S (Q @ K^T):")
print(S)
# 预期：
# [[1, 0, 1],
#  [1, 1, 0],
#  [2, 1, 1]]

# ========== ② 每行做 Softmax ==========
def softmax_row(x):
    """对一维数组做 softmax"""
    e_x = np.exp(x)           # 每个值取 e 的幂
    return e_x / e_x.sum()    # 除以总和

# 对每一行应用 softmax
attention_weights = np.apply_along_axis(softmax_row, axis=1, arr=S)
print("\n② 每行 Softmax 后（Attention Weights）:")
print(attention_weights)
# 验证每行和为 1
print("每行和:", attention_weights.sum(axis=1))

# ========== ③ 加权 V 得到输出 ==========
output = attention_weights @ V
print("\n③ 加权 V 后的输出向量:")
print(output)
