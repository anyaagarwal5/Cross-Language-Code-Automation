import requests
import json
import csv
import re
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from config import polyglot_frontend
from gemini_operations import get_gemini_response

app = FastAPI()

# JDoodle credentials
jdoodle_client_id = "71c468e1a5264f7c2ba0e7575d3bb8b8"
jdoodle_client_secret = "d747f739d92d2b5d9cf248414509e24289d7cb24e6bf97acb85b714ee001085a"


class RefererMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        referer = request.headers.get("referer")
        if referer and referer.startswith(polyglot_frontend['base_url']):
            response = await call_next(request)
            return response
        else:
            return JSONResponse(status_code=403, content={"message": "Forbidden"})

app.add_middleware(RefererMiddleware)

# Mapping programming language with JDoodle language identifier and version
language_version_map = {
    "java": {"language": "java", "versionIndex": "4"},
    "c": {"language": "c", "versionIndex": "5"},
    "cpp": {"language": "cpp", "versionIndex": "5"},
    "javascript": {"language": "nodejs", "versionIndex": "4"},
    "python": {"language": "python3", "versionIndex": "3"},
    "bash": {"language": "bash", "versionIndex": "5"},
    "go": {"language": "go", "versionIndex": "3"},
    "swift": {"language": "swift", "versionIndex": "5"},
    "ruby": {"language": "ruby", "versionIndex": "3"},
    "perl": {"language": "perl", "versionIndex": "3"},
    "php": {"language": "php", "versionIndex": "3"},
    "r": {"language": "r", "versionIndex": "4"},
    "rust": {"language": "rust", "versionIndex": "4"}
}

def execute_code_jdoodle(code, inputVal, language, versionIndex):
    url = "https://api.jdoodle.com/v1/execute"

    payload = {
        "script": code,
        "language": language,
        "versionIndex": versionIndex,
        "stdin": inputVal,
        "clientId": jdoodle_client_id,
        "clientSecret": jdoodle_client_secret
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        return response.json().get("output"), response.json().get("statusCode")
    else:
        return "Error executing code", response.status_code

# Load CSV patterns into memory
def load_patterns():
    patterns = {}
    with open("common_programming_patterns.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            lang_from = row["source_language"]
            lang_to = row["target_language"]
            pattern_from = row["source_code"]
            pattern_to = row["target_code"]
            
            if lang_from not in patterns:
                patterns[lang_from] = {}
            patterns[lang_from][lang_to] = (pattern_from, pattern_to)
    
    return patterns

patterns = load_patterns()

# Code conversion logic using the loaded patterns
def convert_code_using_patterns(source_code, source_lang, target_lang):
    if source_lang not in patterns or target_lang not in patterns[source_lang]:
        return None
    
    pattern_from, pattern_to = patterns[source_lang][target_lang]
    
    # Replace source code patterns with corresponding target language patterns
    converted_code = re.sub(pattern_from, pattern_to, source_code)
    return converted_code

class ExecuteCodeReq(BaseModel):
    code: str
    inputVal: str
    language: str

@app.post("/api/v1/execute-code")
async def get_execute_output(req: ExecuteCodeReq):
    if req.language not in language_version_map.keys():
        return JSONResponse({"status": "failed", "status_code": 400, "error": "Unsupported Programming Language", "message": "Unsupported Programming language"})

    lang_info = language_version_map[req.language]
    output, status_code = execute_code_jdoodle(req.code, req.inputVal, lang_info["language"], lang_info["versionIndex"])
    
    if status_code != 200:
        return JSONResponse({"status": "failed", "status_code": 400, "error": output})
    
    return JSONResponse({"status": "success", "status_code": 200, "data": output})

class CodeConvertReq(BaseModel):
    code: str
    language: str
    source_language: str

@app.post("/api/v1/code-convert")
async def convert_code(req: CodeConvertReq):
    # Attempt to convert code using local patterns first
    converted_code = convert_code_using_patterns(req.code, req.source_language, req.language)
    
    if converted_code:
        return JSONResponse({"status": "success", "status_code": 200, "data": converted_code})
    
    # Fallback: Use Gemini API if no patterns found
    prompt = f'''Convert the following {req.source_language} code into {req.language} code, which is supported by the JDoodle platform for execution. The code should not have any module system issues (like using `import` in JavaScript or missing headers in C/C++). Ensure that the code is executable without requiring additional setup, configurations, or environment changes.
    
    Please make sure the code follows the correct syntax for JDoodle's version of {req.language}, and includes any necessary imports, headers, or default configurations. Also, avoid using any features that require external modules that are not available in JDoodle's environment.

    Here is the source code:

    {req.code}
    '''
    
    res = get_gemini_response(prompt)
    
    # Return the response from Gemini after processing
    return JSONResponse({"status": "success", "status_code": 200, "data": res})

class OptimizeCodeReq(BaseModel):
    code: str
    language: str

@app.post("/api/v1/code-optimize")
async def optimize_code(req: OptimizeCodeReq):
    prompt = f'''give me optimized full working code in {req.language} programming language for below code, give me only code not text \n {req.code}''';
    res = get_gemini_response(prompt)
    return JSONResponse({"status": "success", "status_code": 200, "data": res})

class CodeSuggestionReq(BaseModel):
    code: str

@app.post("/api/v1/code-suggestion")
async def get_suggestions(req: CodeSuggestionReq):
    prompt = f'''give me only suggestions and area of improvement for below code, give me only text \n {req.code}'''
    res = get_gemini_response(prompt)
    return JSONResponse({"status": "success", "status_code": 200, "data": res})

class CodeComplexityReq(BaseModel):
    code: str
    language: str

@app.post("/api/v1/code-complexity")
async def get_code_complexity(req: CodeComplexityReq):
    # Prompt for complexity
    prompt = f'''Analyze the following {req.language} code and give both time and space complexity, with a brief explanation. The explanation should focus on high-level performance, not implementation details.

    Here is the code:
    {req.code}'''

    res = get_gemini_response(prompt)

    return JSONResponse({"status": "success", "status_code": 200, "data": res})

