"""图片混淆 - 算法快速测试"""
import subprocess, sys

# Run the test in a fresh subprocess with uv
cmd = [
    sys.executable, "-c",
    "import math, hashlib, json\n"
    "# 仅测试纯Python部分，不导入numpy\n"
    "def pack(r,g,b): return (r<<16)|(g<<8)|b\n"
    "def md5_s(l,k):\n"
    "    a=list(range(l))\n"
    "    for i in range(l-1,0,-1):\n"
    "        d=hashlib.md5(f'{k}{i}'.encode()).hexdigest()\n"
    "        rn=int(d[:7],16)%(i+1)\n"
    "        a[rn],a[i]=a[i],a[rn]\n"
    "    return a\n"
    "print('pure python: md5_shuffle OK', md5_s(10,'test')[:5])\n"
]

r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
print(r.stdout or r.stderr)
print("---")
print("Exit:", r.returncode)
