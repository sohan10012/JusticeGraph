import json
import urllib.request

try:
    with urllib.request.urlopen('http://localhost:8000/openapi.json') as response:
        data = json.loads(response.read().decode())
    
    with open('api.txt', 'w') as f:
        f.write("========================================================\n")
        f.write("               NYAYMARG API DOCUMENTATION               \n")
        f.write("========================================================\n\n")
        f.write("Base URL: http://localhost:8000\n\n")
        f.write("This document provides a clean and simple overview of all API endpoints,\n")
        f.write("their parameters, and what they return to help with integration.\n\n")

        for path, methods in data.get('paths', {}).items():
            for method, details in methods.items():
                f.write("--------------------------------------------------------\n")
                f.write(f"{method.upper()} {path}\n")
                
                summary = details.get('summary', '')
                if summary:
                    f.write(f"{summary}\n\n")
                
                desc = details.get('description', '')
                if desc:
                    f.write(f"{desc}\n\n")
                
                parameters = details.get('parameters', [])
                if parameters:
                    f.write("Parameters:\n")
                    f.write(f"{'Name':<20} | {'Located In':<10} | {'Required':<8} | {'Type':<10} | Description\n")
                    f.write("-" * 80 + "\n")
                    for p in parameters:
                        name = p.get('name', '')
                        in_loc = p.get('in', '')
                        required = 'Yes' if p.get('required') else 'No'
                        schema = p.get('schema', {})
                        p_type = schema.get('type', '')
                        p_desc = p.get('description', '')
                        if not p_desc:
                            p_desc = 'No description'
                        # clean up desc newlines
                        p_desc = p_desc.replace('\n', ' ')
                        f.write(f"{name:<20} | {in_loc:<10} | {required:<8} | {p_type:<10} | {p_desc}\n")
                    f.write("\n")
                
                request_body = details.get('requestBody', {})
                if request_body:
                    f.write("Request Body:\n")
                    content = request_body.get('content', {})
                    for content_type, content_details in content.items():
                        f.write(f"  Content-Type: {content_type}\n")
                    f.write("  See Swagger UI for exact schema.\n\n")

                responses = details.get('responses', {})
                if responses:
                    f.write("Responses:\n")
                    for code, resp_details in responses.items():
                        r_desc = resp_details.get('description', '')
                        f.write(f"  {code}: {r_desc}\n")
                
                f.write("\nExample usage (Curl):\n")
                example_url = f"http://localhost:8000{path}"
                for p in parameters:
                    if p.get('in') == 'path':
                        example_url = example_url.replace(f"{{{p.get('name')}}}", "example_id")
                
                curl_cmd = f"curl -X '{method.upper()}' \\\n  '{example_url}' \\\n  -H 'accept: application/json'"
                
                # Check auth
                security = details.get('security', [])
                if security:
                    curl_cmd += " \\\n  -H 'Authorization: Bearer <token>'"
                
                f.write(curl_cmd + "\n\n")
                f.write("========================================================\n\n")

    print("api.txt generated successfully!")
except Exception as e:
    print(f"Error: {e}")
