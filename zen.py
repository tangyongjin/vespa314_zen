import uvicorn,os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
# 导入子路由
from ARouters import chan 

tags_metadata = [{"name":"stock","description":"ZenFramework-Vespa314"}]

 
app = FastAPI(
    title="ZenFramework-Vespa314",
    description="fork from Vespa314,move from matplotlib  to pyecharts",
    version="0.0.1",
    tags_metadata=tags_metadata
)


origins = ["*"]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"],)


# 添加子路由
app.include_router(chan)

## 静态文件
app.mount('/public', StaticFiles(directory="public"), 'public')

@app.get("/")
async def root():
    return {"message": "Hello pi"}



if __name__ == "__main__":
    uvicorn.run(app="zen:app", host="127.0.0.1", debug=True, reload=True)
 