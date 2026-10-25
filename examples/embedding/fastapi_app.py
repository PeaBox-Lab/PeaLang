

from fastapi import FastAPI
from pydantic import BaseModel
from pealang import PeaRuntime, RuntimeOptions
app=FastAPI(title='PeaLang extension example')
runtime=PeaRuntime(RuntimeOptions(max_execution_ms=250,max_instructions=10_000))
rules=runtime.load_file('bonus_rules.pea')
class Employee(BaseModel):
    rating:int
    salary:float
@app.post('/bonus')
def bonus(employee:Employee):
    return {'bonus':rules.call('calculate_bonus',employee)}


