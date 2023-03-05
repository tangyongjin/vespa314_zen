import os
import sys
import json
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from django.http import HttpResponse
import tushare as ts  
from Actions.ZTest import  ZTest

chan = APIRouter(
    prefix="/chan",
    tags=["ZenData-Json"],
    responses={404: {"description": "chan222"}}
)


@chan.post('/ZenTest')
async def ZenTest(item: dict):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    
    
    # json_compatible_item_data = jsonable_encoder({"code":200,"charts":['aa','bb']})
    json_compatible_item_data=await ZTest()
    # print(json_compatible_item_data )
    # return json.dumps(json_compatible_item_data)
    return JSONResponse(  {"code":200,"echartsData": json_compatible_item_data }  )
 

 
 