import requests
class LocalModel:
    def __init__(self,url="http://127.0.0.1:8080/v1/chat/completions"):
        self.url=url
    def available(self):
        try: return requests.get(self.url.rsplit("/v1/",1)[0]+"/health",timeout=2).ok
        except Exception: return False
    def chat(self,text,system=None):
        messages=([{"role":"system","content":system}] if system else [])+[{"role":"user","content":text}]
        try:
            r=requests.post(self.url,json={"messages":messages,"temperature":0.7,"max_tokens":300,"stream":False},timeout=30)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception: return None
