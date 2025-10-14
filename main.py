from flask import Flask, render_template, request, jsonify
from global_view_sql_query import execute_query
from llm_backend import generate_sql_query

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def run_query():
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    results = execute_query(query)
    
    if results is None:
        return jsonify({'error': 'Database error occurred'}), 500
    
    return jsonify({'results': results, 'count': len(results)})

@app.route('/llm-query', methods=['POST'])
def run_llm_query():
    data = request.get_json()
    user_input = data.get('input')
    
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400
    
    # Generate SQL query from natural language
    sql_query = generate_sql_query(user_input)
    
    if not sql_query:
        return jsonify({'error': 'Failed to generate SQL query'}), 500
    
    # Execute the generated SQL query
    results = execute_query(sql_query)
    
    if results is None:
        return jsonify({'error': 'Database error occurred'}), 500
    
    return jsonify({
        'sql_query': sql_query,
        'results': results, 
        'count': len(results)
    })

if __name__ == '__main__':
    app.run(debug=True)

