import ast,os
class SelfModel:
    def inspect(self,root):
        r={"root":root,"python_files":0,"classes":0,"functions":0,"errors":0}
        for directory,_,files in os.walk(root):
            for name in files:
                if not name.endswith(".py"):continue
                r["python_files"]+=1
                try:
                    with open(os.path.join(directory,name),encoding="utf-8") as f:tree=ast.parse(f.read())
                    for n in ast.walk(tree):
                        if isinstance(n,ast.ClassDef):r["classes"]+=1
                        elif isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):r["functions"]+=1
                except Exception:r["errors"]+=1
        return r
