import os,time
class SelfCoder:
    def __init__(self,root):self.root=os.path.abspath(root)
    def create_proposal(self,description,patch_text):
        d=os.path.join(self.root,"updates","proposals");os.makedirs(d,exist_ok=True)
        p=os.path.join(d,f"proposal_{int(time.time())}.patch")
        with open(p,"w",encoding="utf-8") as f:f.write("# VIN SELF-IMPROVEMENT PROPOSAL\n# "+description+"\n\n"+patch_text)
        return p
