"""
练习 0-2：梯度下降
对 f(x,y) = x^2 + 2xy + 3y^2 做梯度下降
"""

def f(x, y):
    return x**2 + 2*x*y + 3*y**2

x, y = 3.0, 2.0
lr = 0.1

print(f"{'步':>3}  {'x':>8}  {'y':>8}  {'f(x,y)':>10}")
print("-" * 35)

for step in range(21):
    if step == 0:
        print(f"{step:>3}  {x:>8.4f}  {y:>8.4f}  {f(x,y):>10.4f}")
    else:
        dx = 2*x + 2*y    # ∂f/∂x = 坡度
        dy = 2*x + 6*y    # ∂f/∂y = 坡度
        x = x - lr * dx   # 往下走一步
        y = y - lr * dy
        print(f"{step:>3}  {x:>8.4f}  {y:>8.4f}  {f(x,y):>10.4f}")
