import json,os,time
class SelfLearning:
    def __init__(self,root):
        self.file=os.path.join(root,"learning","knowledge.json"); os.makedirs(os.path.dirname(self.file),exist_ok=True)
        if not os.path.exists(self.file): self._save({"observations":[],"lessons":[]})
    def _load(self):
        try:
            with open(self.file,encoding="utf-8") as f:d=json.load(f)
            d.setdefault("observations",[]); d.setdefault("lessons",[]); return d
        except Exception:return {"observations":[],"lessons":[]}
    def _save(self,d):
        t=self.file+".tmp"
        with open(t,"w",encoding="utf-8") as f:json.dump(d,f,indent=2,ensure_ascii=False)
        os.replace(t,self.file)
    def observe(self,text):
        d=self._load(); d["observations"].append({"text":text,"time":time.time()}); d["observations"]=d["observations"][-100:]; self._save(d)
    def add_lesson(self,lesson):
        d=self._load()
        if lesson not in d["lessons"]:d["lessons"].append(lesson)
        d["lessons"]=d["lessons"][-100:]; self._save(d)
    def status(self):
        d=self._load(); return f"Observations: {len(d['observations'])}\nLessons: {len(d['lessons'])}"
