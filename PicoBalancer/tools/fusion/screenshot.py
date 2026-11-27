"""python screenshot.py out.png [width height] - PNG of the active Fusion viewport."""
import base64, json, sys
from fusion_mcp import post
sid,_=post({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"pb","version":"1"}}})
post({"jsonrpc":"2.0","method":"notifications/initialized"},sid)
w,h=(int(sys.argv[2]),int(sys.argv[3])) if len(sys.argv)>3 else (900,1400)
_,out=post({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"fusion_mcp_read","arguments":{"queryType":"screenshot","width":w,"height":h}}},sid)
d=json.loads(out)
for c in d.get('result',{}).get('content',[]):
    if c.get('type')=='image':
        open(sys.argv[1],'wb').write(base64.b64decode(c['data'])); print('saved',sys.argv[1]); break
    t=c.get('text','')
    try:
        j=json.loads(t)
        for k in ('image','png','data','base64'):
            if k in j: open(sys.argv[1],'wb').write(base64.b64decode(j[k])); print('saved',sys.argv[1]); break
        else: print(t[:300])
    except Exception: print(t[:300])
