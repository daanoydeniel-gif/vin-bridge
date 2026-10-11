import json,os,time
class PermissionManager:
    def __init__(self,root):
        self.file=os.path.join(root,"security","permissions.json"); os.makedirs(os.path.dirname(self.file),exist_ok=True)
        if not os.path.exists(self.file): self._save({"next_id":1,"pending":[],"approved":[]})
    def _load(self):
        try:
            with open(self.file,encoding="utf-8") as f:d=json.load(f)
            d.setdefault("next_id",1); d.setdefault("pending",[]); d.setdefault("approved",[]); return d
        except Exception:return {"next_id":1,"pending":[],"approved":[]}
    def _save(self,d):
        t=self.file+".tmp"
        with open(t,"w",encoding="utf-8") as f:json.dump(d,f,indent=2)
        os.replace(t,self.file)
    def request(self,action,target):
        d=self._load(); i=d["next_id"]; d["next_id"]+=1
        d["pending"].append({"id":i,"action":action,"target":target,"time":time.time()}); self._save(d); return i
    def pending(self): return self._load()["pending"]
    def allow(self,i):
        d=self._load()
        for x in d["pending"]:
            if x["id"]==i:
                d["pending"].remove(x); d["approved"].append(x); self._save(d)
                return f"PERMISSION APPROVED\nID: {x['id']}\nAction: {x['action']}\nTarget: {x['target']}"
        return "Permission request not found."
    def deny(self,i):
        d=self._load()
        for x in d["pending"]:
            if x["id"]==i:
                d["pending"].remove(x); self._save(d)
                return f"PERMISSION DENIED\nID: {x['id']}\nAction: {x['action']}\nTarget: {x['target']}"
        return "Permission request not found."
    def consume_approved(self,a,t):
        d=self._load()
        for x in d["approved"]:
            if x["action"]==a and x["target"]==t:
                d["approved"].remove(x); self._save(d); return True
        return False
