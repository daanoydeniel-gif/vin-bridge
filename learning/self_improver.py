import py_compile
class SelfImprover:
    def validate_file(self,path):
        try:py_compile.compile(path,doraise=True);return {"valid":True,"message":"Python syntax is valid."}
        except Exception as e:return {"valid":False,"message":str(e)}
