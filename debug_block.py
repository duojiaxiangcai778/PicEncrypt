"""调试块混淆"""
import math, hashlib, random

def pack(r,g,b): return (int(r)<<16)|(int(g)<<8)|int(b)
def md5_s(l,k):
    a=list(range(l))
    for i in range(l-1,0,-1):
        d=hashlib.md5(f'{k}{i}'.encode()).hexdigest()
        rn=int(d[:7],16)%(i+1)
        a[rn],a[i]=a[i],a[rn]
    return a

def block_s(p,w,h,k,en=True):
    xc=min(32,w);yc=min(32,h)
    xa,ya=md5_s(xc,k),md5_s(yc,k)
    nw,nh=w,h
    while nw%xc:nw+=1
    while nh%yc:nh+=1
    bw,bh=nw//xc,nh//yc
    pad=[0]*(nw*nh)
    for y in range(nh):
        for x in range(nw):
            sx=min(x,w-1);sy=min(y,h-1)
            pad[x+y*nw]=p[sx+sy*w]
    new=[0]*(nw*nh)
    if en:
        for i in range(nw):
            for j in range(nh):
                n=j;m=(xa[(n//bh)%xc]*bw+i)%nw
                m=xa[m//bw]*bw+m%bw;n=(ya[m//bw%yc]*bh+n)%nh;n=ya[n//bh]*bh+n%bh
                new[i+j*nw]=pad[m+n*nw]
    else:
        for i in range(nw):
            for j in range(nh):
                n=j;m=(xa[(n//bh)%xc]*bw+i)%nw
                m=xa[m//bw]*bw+m%bw;n=(ya[m//bw%yc]*bh+n)%nh;n=ya[n//bh]*bh+n%bh
                new[m+n*nw]=pad[i+j*nw]
    return new,nw,nh

# Test specific failing cases
cases = [(50,25),(54,51),(46,13),(80,60),(50,100),(99,77)]
for w,h in cases:
    px=[pack((x*7)%256,(y*13)%256,(x+y)%256) for y in range(h) for x in range(w)]
    epx,ew,eh=block_s(px,w,h,"key",en=True)
    dpx,dw,dh=block_s(epx,ew,eh,"key",en=False)
    m=sum(1 for i in range(len(px)) if dpx[i]==px[i])
    t=len(px)
    print(f"{w}x{h}: {m}/{t} match {'OK' if m==t else 'FAIL'}")
    if m!=t:
        # Find first mismatch
        for i in range(t):
            if dpx[i]!=px[i]:
                enc_i = i  # position in encrypted output
                # find where this pixel came from in enc
                print(f"  First mismatch at pixel {i}: orig={px[i]:06x}, dec={dpx[i]:06x}")
                break

print()
print("Testing with uniform pixels (all same)...")
for w,h in cases:
    px=[pack(128,128,128) for _ in range(w*h)]
    epx,ew,eh=block_s(px,w,h,"key",en=True)
    dpx,dw,dh=block_s(epx,ew,eh,"key",en=False)
    m=sum(1 for i in range(len(px)) if dpx[i]==px[i])
    print(f"{w}x{h}: {m}/{len(px)} match")
