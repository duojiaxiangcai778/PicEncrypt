"""图片混淆算法 纯Python测试（不用numpy）"""
import math, hashlib, time, random

def pack(r,g,b): return (int(r)<<16)|(int(g)<<8)|int(b)
def md5_s(l,k):
    a=list(range(l))
    for i in range(l-1,0,-1):
        d=hashlib.md5(f'{k}{i}'.encode()).hexdigest()
        rn=int(d[:7],16)%(i+1)
        a[rn],a[i]=a[i],a[rn]
    return a

def gilbert(w,h):
    pc=w*h; pos=[0]*pc; p=[0]
    def gd(x,y,ax,ay,bx,by):
        w_,h_=abs(ax+ay),abs(bx+by)
        dax=int(math.copysign(1,ax)) if ax else 0
        day=int(math.copysign(1,ay)) if ay else 0
        dbx=int(math.copysign(1,bx)) if bx else 0
        dby=int(math.copysign(1,by)) if by else 0
        if h_==1:
            for _ in range(w_): pos[p[0]]=x+y*w; p[0]+=1; x+=dax; y+=day
            return
        if w_==1:
            for _ in range(h_): pos[p[0]]=x+y*w; p[0]+=1; x+=dbx; y+=dby
            return
        a2x,a2y=ax//2,ay//2; b2x,b2y=bx//2,by//2
        if 2*w_>3*h_:
            if (abs(a2x+a2y)&1)==1 and w_>2: a2x+=dax;a2y+=day
            gd(x,y,a2x,a2y,bx,by);gd(x+a2x,y+a2y,ax-a2x,ay-a2y,bx,by)
        else:
            if (abs(b2x+b2y)&1)==1 and h_>2: b2x+=dbx;b2y+=dby
            gd(x,y,b2x,b2y,a2x,a2y);gd(x+b2x,y+b2y,ax,ay,bx-b2x,by-b2y)
            gd(x+(ax-dax)+(b2x-dbx),y+(ay-day)+(b2y-dby),-b2x,-b2y,-(ax-a2x),-(ay-a2y))
    if w>=h: gd(0,0,w,0,0,h)
    else: gd(0,0,0,h,w,0)
    return pos

def tomato(p,w,h,k,en=True):
    n=len(p); off=int(round((math.sqrt(5)-1)/2*n*k))
    pos=gilbert(w,h); lp=n-off; new=[0]*n
    if en:
        for i in range(lp): new[pos[i+off]]=p[pos[i]]
        for i in range(lp,n): new[pos[i-lp]]=p[pos[i]]
    else:
        for i in range(lp): new[pos[i]]=p[pos[i+off]]
        for i in range(lp,n): new[pos[i]]=p[pos[i-lp]]
    return new,w,h

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

def row_s(p,w,h,k,en=True):
    xa=md5_s(w,k);new=[0]*len(p)
    if en:
        for i in range(w):
            for j in range(h):m=xa[(xa[j%w]+i)%w];new[i+j*w]=p[m+j*w]
    else:
        for i in range(w):
            for j in range(h):m=xa[(xa[j%w]+i)%w];new[m+j*w]=p[i+j*w]
    return new,w,h

def per_s(p,w,h,k,en=True):
    xa,ya=md5_s(w,k),md5_s(h,k);new=[0]*len(p)
    if en:
        for i in range(w):
            for j in range(h):
                m=xa[(xa[j%w]+i)%w];n=ya[(ya[m%h]+j)%h]
                new[i+j*w]=p[m+n*w]
    else:
        for i in range(w):
            for j in range(h):
                m=xa[(xa[j%w]+i)%w];n=ya[(ya[m%h]+j)%h]
                new[m+n*w]=p[i+j*w]
    return new,w,h

def logi(x1,n):
    a=[(0.0,0)]*n;x=x1
    for i in range(1,n):x=3.9999999*x*(1-x);a[i]=(x,i)
    return a

def getpos(lm):
    n=len(lm);si=sorted(range(n),key=lambda i:lm[i][0])
    return [int(lm[si[i]][1]) for i in range(n)]

def pecrow(p,w,h,k,en=True):
    lm=logi(k,w);pos=getpos(lm);new=[0]*len(p);off=(h-1)*w
    if en:
        for i in range(w):
            m=pos[i]
            for j in range(off,-1,-w): new[i+j]=p[m+j]
    else:
        for i in range(w):
            m=pos[i]
            for j in range(off,-1,-w): new[m+j]=p[i+j]
    return new,w,h

def pecrowcol(p,w,h,k,en=True):
    P=list(p);T=list(p)
    if en:
        x=k
        for j in range(h):
            off=j*w;lm=logi(x,w);x=lm[w-1][0];pos=getpos(lm)
            for i in range(w):P[i+off]=T[pos[i]+off]
        x=k
        for i in range(w):
            lm=logi(x,h);x=lm[h-1][0];pos=getpos(lm)
            for j in range(h):T[i+j*w]=P[i+pos[j]*w]
    else:
        x=k
        for i in range(w):
            lm=logi(x,h);x=lm[h-1][0];pos=getpos(lm)
            for j in range(h):P[i+pos[j]*w]=T[i+j*w]
        x=k
        for j in range(h):
            off=j*w;lm=logi(x,w);x=lm[w-1][0];pos=getpos(lm)
            for i in range(w):T[pos[i]+off]=P[i+off]
    return T,w,h

ALGOS=[(tomato,0.5,'番茄'),(block_s,'key','块'),(row_s,'key','行像素'),(per_s,'key','逐像素'),(pecrow,0.5,'行模式'),(pecrowcol,0.5,'行+列')]

t0=time.time()
print("=== 第四轮: 随机尺寸 ===")
random.seed(42)
ok4=True
for ti in range(6):
    w,h=random.randint(8,80),random.randint(8,80)
    px=[pack(random.randint(0,255),random.randint(0,255),random.randint(0,255)) for _ in range(w*h)]
    for fn,kw,name in ALGOS:
        ek=kw+0.01*ti if isinstance(kw,float) else kw
        epx,ew,eh=fn(px,w,h,ek,en=True)
        dpx,dw,dh=fn(epx,ew,eh,ek,en=False)
        # 解密结果布局为 dw×dh，原始布局为 w×h
        ok=True
        for y in range(h):
            for x in range(w):
                if dpx[y*dw+x]!=px[y*w+x]:
                    ok=False;break
            if not ok:break
        if not ok:ok4=False;print("  FAIL:",name,w,"x",h)
if ok4:print("  OK - 随机尺寸全部通过")

print("=== 第五轮: 矩形/非对齐尺寸 ===")
ok5=True
for w,h in [(80,60),(128,72),(50,100),(31,47),(99,77)]:
    px=[pack((x*7)%256,(y*13)%256,(x+y)%256) for y in range(h) for x in range(w)]
    for fn,kw,name in ALGOS:
        ek=kw if isinstance(kw,str) else kw
        epx,ew,eh=fn(px,w,h,ek,en=True)
        dpx,dw,dh=fn(epx,ew,eh,ek,en=False)
        ok=True
        for y in range(h):
            for x in range(w):
                if dpx[y*dw+x]!=px[y*w+x]:
                    ok=False;break
            if not ok:break
        if not ok:ok5=False;print("  FAIL:",name,w,"x",h)
if ok5:print("  OK - 矩形/非对齐全部通过")

elapsed=time.time()-t0
print()
print("耗时:", round(elapsed,1), "s")
if ok4 and ok5:
    print("OK - 全部通过!")
else:
    print("FAIL - 有错误!")
