"""
算法可逆性测试 — 验证 encrypt+decrypt 后图片100%恢复

注意：decrypt 结果可能因padding而有不同尺寸 (dw×dh)，
比较时必须用 dw 索引，不能假设返回原始尺寸。
"""
import math, hashlib, time, random, sys

def pack(r,g,b): return (int(r)<<16)|(int(g)<<8)|int(b)

# ... (所有算法函数略，同 pure_test.py)

# 测试正确索引方式
def check_reversible(fn, px, w, h, key):
    epx, ew, eh = fn(px, w, h, key, encrypt=True)
    dpx, dw, dh = fn(epx, ew, eh, key, encrypt=False)
    for y in range(h):
        for x in range(w):
            if dpx[y*dw + x] != px[y*w + x]:
                return False
    return True
