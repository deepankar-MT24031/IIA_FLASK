from flask import Flask, render_template, request, jsonify
from global_view_sql_query import execute_query

from system_prompt_one import system_prompt_1
from system_prompt_two import system_prompt_2
from system_prompt_three import system_prompt_3
from intersection_csv import find_csv_intersection_from_strings


# from llm_backend import generate_sql_query
from nvidia import generate_sql_query

import json
import re
import csv
import io

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


# @app.route('/llm-query', methods=['POST'])
# def run_llm_query():
#     data = request.get_json()
#     user_input = data.get('input')
#
#     if not user_input:
#         return jsonify({'error': 'No input provided'}), 400
#
#     llm_plan = generate_sql_query(user_input)
#     print("Raw llm_plan:", llm_plan)
#
#     # Clean and parse LLM output if it's text
#     if isinstance(llm_plan, str):
#         # Remove markdown JSON fences (```json ... ```)
#         clean = re.sub(r"^```(?:json)?", "", llm_plan.strip(), flags=re.IGNORECASE)
#         clean = re.sub(r"```$", "", clean.strip())
#
#         try:
#             llm_plan = json.loads(clean)
#         except json.JSONDecodeError as e:
#             print("JSON decode error:", e)
#             return jsonify({'error': 'Invalid JSON from LLM'}), 500
#
#     # Step 2: Validate the LLM plan
#     if not llm_plan or not isinstance(llm_plan, dict):
#         print("error: Invalid LLM response: Expected JSON plan")
#         return jsonify({'error': 'Invalid LLM response: Expected JSON plan'}), 500
#
#     database_needed = llm_plan.get('database_needed')
#     sufficient = llm_plan.get('sufficient')
#     sql_query = llm_plan.get('sql_query')
#
#     if not isinstance(database_needed, bool):
#         return jsonify({'error': "Invalid LLM plan: 'database_needed' must be boolean"}), 400
#
#     if not sql_query or not isinstance(sql_query, str) or not sql_query.strip().lower().startswith("select"):
#         return jsonify({'error': "Invalid LLM plan: 'sql_query' missing or not a SELECT query"}), 400
#
#     # Step 3: Run SQL if needed
#     results = []
#     if database_needed:
#         results = execute_query(sql_query)  # <--- uses your existing DB executor
#         if results is None:
#             return jsonify({'error': 'Database error occurred'}), 500
#
#     # Step 4: Decide based on sufficiency
#     if sufficient:
#         # Sufficient: return DB results directly
#         return jsonify({
#             'sql_query': sql_query,
#             'plan': llm_plan,
#             'results': results,
#             'count': len(results)
#         })
#     else:
#         # Insufficient: placeholder for System Prompt-2 (web enrichment etc.)
#         enriched_results = handle_insufficient_case(user_input, results)  # Dummy for now
#         return jsonify({
#             'plan': llm_plan,
#             'results': enriched_results,
#             'count': len(enriched_results),
#             'note': 'Sufficient=false handled via dummy function.'
#         })


@app.route('/llm-query', methods=['POST'])
def run_llm_query():
    # ---------------- STEP 1: Get and validate user input ----------------
    data = request.get_json()
    user_input = data.get('input')

    if not user_input:
        return jsonify({'error': 'No input provided'}), 400


    # ---------------- STEP 2: Get JSON plan from LLM ----------------
    llm_plan = generate_sql_query(user_input, system_prompt_1,1)
    print(":::::::::::::::::Raw JSON :::::::::::", llm_plan)

    # Clean and parse JSON if returned as text
    if isinstance(llm_plan, str):
        clean = re.sub(r"^```(?:json)?", "", llm_plan.strip(), flags=re.IGNORECASE)
        clean = re.sub(r"```$", "", clean.strip())
        try:
            llm_plan = json.loads(clean)
        except json.JSONDecodeError as e:
            print("JSON decode error:", e)
            return jsonify({'error': 'Invalid JSON from LLM'}), 500


    # ---------------- STEP 3: Validate LLM plan ----------------
    if not llm_plan or not isinstance(llm_plan, dict):
        return jsonify({'error': 'Invalid LLM response: Expected JSON plan'}), 500

    database_needed = llm_plan.get('database_needed')
    sufficient = llm_plan.get('sufficient')
    sql_query = llm_plan.get('sql_query')

    if not isinstance(database_needed, bool):
        return jsonify({'error': "Invalid LLM plan: 'database_needed' must be boolean"}), 400
    if not sql_query or not isinstance(sql_query, str) or not sql_query.strip().lower().startswith("select"):
        return jsonify({'error': "Invalid LLM plan: 'sql_query' missing or not a SELECT query"}), 400


    # ---------------- STEP 4: Run SQL if database_needed = True ----------------
    results = []
    csv_output = ""

    if database_needed:
        results = execute_query(sql_query)  # your existing DB executor

        print(":::::::::::ACTUAL RESULT FROM DATABASE::::::")
        print(results)

        if results is None:
            return jsonify({'error': 'Database error occurred'}), 500

        # Convert results (list of dicts) → CSV string
        if results:
            csv_buffer = io.StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
            csv_output = csv_buffer.getvalue()
            csv_buffer.close()

            print(":::::::::: database_needed::::::::::::::OUTPUT")
            print(csv_output)


    if(sufficient == True) and (database_needed == True) and (csv_output == ""):
        print(":::::: SUFFICIENT IS TRUE BUT DATABASE RETURNED EMPTY :::::::::")
        return when_sufficient_is_returning_empty_query_result(user_input)



    # ---------------- STEP 5: If sufficient = True → Return DB CSV directly ----------------
    if sufficient:
        return jsonify({
            'sql_query': sql_query,
            'plan': llm_plan,
            'results': csv_output,   # CSV string
            'count': len(results)
        })


    # ---------------- STEP 6: If sufficient = False → plan to enrichment handler ----------------
    else:
        enriched_response = handle_insufficient_case(llm_plan)


        if (sufficient == False) and (database_needed == True):

            if (sufficient == False) and (results == []):
                return enriched_response



            print(":::::::::: INTERSECTION ::::::::::::::OUTPUT")
            intersection = find_csv_intersection_from_strings(enriched_response["results"],csv_output,threshold=70 )
            print(intersection)


            if intersection == '':
                return enriched_response



        # The handler returns JSON — you forward it directly
        return jsonify({
            'sql_query': sql_query,
            'plan': llm_plan,
            'results': intersection,   # CSV string
            'count': len(results)
        })



def handle_insufficient_case(llm_plan):
    """
    Handles insufficient queries using only the LLM plan.
    - Builds a new user prompt from 'notes' and 'web_fields_needed'
    - Calls the LLM again with the externally provided system prompt
    - Returns a structured JSON with CSV results
    """

    print("Enrichment handler triggered (System Prompt-2).")

    # Extract fields from plan
    notes = llm_plan.get("notes", "")
    web_fields = llm_plan.get("web_fields_needed", [])

    # Build user prompt dynamically
    user_prompt = f"""note: {notes}
web_fields_needed: {json.dumps(web_fields)}"""

    print("Generated user prompt for enrichment:\n", user_prompt)

    # Call the LLM with the combined prompt
    try:
        enriched_csv = generate_sql_query(user_prompt, system_prompt_2,2)  # system_prompt_2 handled externally
    except Exception as e:
        return {
            "error": f"Enrichment LLM call failed: {str(e)}"
        }

    # Clean the LLM's CSV output
    if isinstance(enriched_csv, str):
        clean_csv = re.sub(r"^```(?:csv|json)?", "", enriched_csv.strip(), flags=re.IGNORECASE)
        clean_csv = re.sub(r"```$", "", clean_csv.strip())
    else:
        clean_csv = str(enriched_csv)

    print(":::::::::: LLM SYSTEM PROMPT NEEDED = True::::::::::::::OUTPUT")
    print("Enriched CSV output preview:\n", clean_csv)








    # Return unified JSON response
    return {
        "plan": {
            "web_fields_needed": web_fields,
            "notes": notes
        },
        "results": clean_csv,
        "count": clean_csv.count('\n') - 1,
        "note": "Sufficient=false handled by System Prompt-3 enrichment."
    }

def when_sufficient_is_returning_empty_query_result(user_input):
    """
    Handles insufficient queries using only the LLM plan.
    - Builds a new user prompt from 'notes' and 'web_fields_needed'
    - Calls the LLM again with the externally provided system prompt
    - Returns a structured JSON with CSV results
    """

    print("Enrichment handler triggered (System Prompt-3).")

    # Extract fields from plan
    # notes = llm_plan.get("notes", "")
    # web_fields = llm_plan.get("web_fields_needed", [])

    # Build user prompt dynamically
#     user_prompt = f"""note: {notes}
# web_fields_needed: {json.dumps(web_fields)}"""

    # print("Generated user prompt for enrichment:\n", user_prompt)

    # Call the LLM with the combined prompt
    try:
        enriched_csv = generate_sql_query(user_input, system_prompt_3,3)  # system_prompt_2 handled externally
    except Exception as e:
        return {
            "error": f"Enrichment LLM call failed: {str(e)}"
        }

    # Clean the LLM's CSV output
    if isinstance(enriched_csv, str):
        clean_csv = re.sub(r"^```(?:csv|json)?", "", enriched_csv.strip(), flags=re.IGNORECASE)
        clean_csv = re.sub(r"```$", "", clean_csv.strip())
    else:
        clean_csv = str(enriched_csv)

    print(":::::::::: LLM SYSTEM PROMPT NEEDED = True::::::::::::::OUTPUT")
    print("Enriched CSV output preview:\n", clean_csv)

    # Return unified JSON response
    return {
        "plan": {
            "web_fields_needed": "",
            "notes": ""
        },
        "results": clean_csv,
        "count": clean_csv.count('\n') - 1,
        "note": "Sufficient=false handled by System Prompt-3 enrichment."
    }

if __name__ == '__main__':
    app.run(debug=True)

