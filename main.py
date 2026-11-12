import requests
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from gemini_operations import get_gemini_response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from config import polyglot_frontend


app = FastAPI()

# JDoodle credentials
jdoodle_client_id = "71c468e1a5264f7c2ba0e7575d3bb8b8"
jdoodle_client_secret = "d747f739d92d2b5d9cf248414509e24289d7cb24e6bf97acb85b714ee001085a"

origins = [
    polyglot_frontend['base_url'],
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

#Mapping programming language with its file extension
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
    if not req.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty.")
    if not req.language.strip():
        raise HTTPException(status_code=400, detail="Language must be specified.")

    # Improved Prompt
    prompt = f"""
Analyze the following {req.language} code and provide:
1. **Time Complexity:** Explain with Big-O notation.
2. **Space Complexity:** Explain with Big-O notation.
3. **Explanation:** A brief, high-level reasoning for the complexities.

Code:
{req.code}

Return the response in the following structured format:
Time Complexity: O(...)
Space Complexity: O(...)
Explanation: ...
"""

    res = get_gemini_response(prompt)

    return JSONResponse({"status": "success", "status_code": 200, "data": res})
