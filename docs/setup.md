1. Install package
Run this command to install the required dependencies.
Code:
File: Code
```
pip install supabase
```

2. Add files
Copy the following code into your project.
Code:
File: .env
```
SUPABASE_URL=https://uqsojovjjzgzbvkfzgfz.supabase.co
SUPABASE_KEY=sb_publishable_CuV53k9jmrsAzNkkkip9IQ_yZVg7kvO
```

File: app.py
```
1import os
2from flask import Flask
3from supabase import create_client, Client
4from dotenv import load_dotenv
5
6load_dotenv()
7
8app = Flask(__name__)
9
10supabase: Client = create_client(
11    os.environ.get("SUPABASE_URL"),
12    os.environ.get("SUPABASE_KEY")
13)
14
15@app.route('/')
16def index():
17    response = supabase.table('todos').select("*").execute()
18    todos = response.data
19
20    html = '<h1>Todos</h1><ul>'
21    for todo in todos:
22        html += f'<li>{todo["name"]}</li>'
23    html += '</ul>'
24
25    return html
26
27if __name__ == '__main__':
28    app.run(debug=True)
```

3. Install Agent Skills (optional)
Agent Skills give AI coding tools ready-made instructions, scripts, and resources for working with Supabase more accurately and efficiently.
Code:
File: Code
```
npx skills add supabase/agent-skills
```