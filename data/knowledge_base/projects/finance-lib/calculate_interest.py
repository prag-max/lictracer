# 来自 finance-lib：复利计算函数（GPL-3.0）
def calculate_interest(principal, rate, time):
    return principal * (1 + rate) ** time