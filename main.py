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

# @app.route('/llm-query', methods=['POST'])
# def run_llm_query():
#     data = request.get_json()
#     user_input = data.get('input')
#
#     if not user_input:
#         return jsonify({'error': 'No input provided'}), 400
#
#     # Generate SQL query from natural language
#     sql_query = generate_sql_query(user_input)
#
#     if not sql_query:
#         return jsonify({'error': 'Failed to generate SQL query'}), 500
#
#     # Execute the generated SQL query
#     results = execute_query(sql_query)
#
#     if results is None:
#         return jsonify({'error': 'Database error occurred'}), 500
#
#     return jsonify({
#         'sql_query': sql_query,
#         'results': results,
#         'count': len(results)
#     })


@app.route('/llm-query', methods=['POST'])
def run_llm_query():
    data = request.get_json()
    user_input = data.get('input')

    if not user_input:
        return jsonify({'error': 'No input provided'}), 400

    # Step 1: Get the JSON plan from the LLM (System Prompt-1)
    #llm_plan = generate_llm_json_plan(user_input)  # This replaces generate_sql_query()

    llm_plan = {
                  "database_needed": True,
                  "sufficient": True,
                  "sql_query": "SELECT c.title FROM global_views.global_content c WHERE NULLIF(regexp_replace(SUBSTR(c.release_date,1,4),'[^0-9]','','g'),'')::int > 2015 AND c.content_type = 'tv' LIMIT 10;",
                  "fields_expected_from_db": ["content_global_id","title","release_date","content_type","source_schema"],
                  "web_search_needed": False,
                  "web_fields_needed": [],
                  "very_large_result": False,
                  "notes": ""
                }

    # Step 2: Validate the LLM plan
    if not llm_plan or not isinstance(llm_plan, dict):
        return jsonify({'error': 'Invalid LLM response: Expected JSON plan'}), 500

    database_needed = llm_plan.get('database_needed')
    sufficient = llm_plan.get('sufficient')
    sql_query = llm_plan.get('sql_query')

    if not isinstance(database_needed, bool):
        return jsonify({'error': "Invalid LLM plan: 'database_needed' must be boolean"}), 400

    if not sql_query or not isinstance(sql_query, str) or not sql_query.strip().lower().startswith("select"):
        return jsonify({'error': "Invalid LLM plan: 'sql_query' missing or not a SELECT query"}), 400

    # Step 3: Run SQL if needed
    results = []
    if database_needed:
        results = execute_query(sql_query)  # <--- uses your existing DB executor
        if results is None:
            return jsonify({'error': 'Database error occurred'}), 500

    # Step 4: Decide based on sufficiency
    if sufficient:
        # Sufficient: return DB results directly
        return jsonify({
            'sql_query': sql_query,
            'plan': llm_plan,
            'results': results,
            'count': len(results)
        })
    else:
        # Insufficient: placeholder for System Prompt-2 (web enrichment etc.)
        enriched_results = handle_insufficient_case(user_input, results)  # Dummy for now
        return jsonify({
            'plan': llm_plan,
            'results': enriched_results,
            'count': len(enriched_results),
            'note': 'Sufficient=false handled via dummy function.'
        })


# Dummy placeholder for future web enrichment step
def handle_insufficient_case(user_query, db_results):
    """
    This will later call System Prompt-2 with user_query + db_rows JSON,
    fetch web data, merge results, and return the enriched list.
    Currently acts as a placeholder.
    """
    return db_results


if __name__ == '__main__':
    app.run(debug=True)

