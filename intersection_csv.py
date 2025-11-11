from io import StringIO
import pandas as pd
import re
import unicodedata
from rapidfuzz import process, fuzz

def find_csv_intersection_from_strings(csv_str1: str,
                                       csv_str2: str,
                                       threshold: int = 85) -> str:
    """
    Take two CSVs as strings, return intersection (only from CSV1) as a CSV string.
    - Performs normalized exact match first.
    - If exact returns zero rows, performs fuzzy matching with given threshold.
    - Returns CSV string (empty string if no matches found).
    """

    print(":::::CSV1:::::\n", csv_str1)
    print(":::::CSV2:::::\n", csv_str2)

    # --- helper: normalize titles ---
    def normalize_title(s):
        if pd.isna(s):
            return ''
        s = str(s)
        s = unicodedata.normalize('NFKD', s)
        s = s.encode('ascii', 'ignore').decode('ascii')
        s = re.sub(r'[^\w\s]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip().lower()
        if s.startswith('the '):
            s = s[4:]
        return s

    # --- read CSV strings ---
    df1 = pd.read_csv(StringIO(csv_str1), skipinitialspace=True, dtype=str)
    df2 = pd.read_csv(StringIO(csv_str2), skipinitialspace=True, dtype=str)

    # ensure 'title' column exists
    if 'title' not in df1.columns or 'title' not in df2.columns:
        raise ValueError("Both CSV inputs must contain a 'title' column.")

    # normalize title
    df1['title_norm'] = df1['title'].map(normalize_title)
    df2['title_norm'] = df2['title'].map(normalize_title)

    # ------------------------
    # 1️⃣ Exact (normalized) match
    # ------------------------
    matched_titles = set(df2['title_norm'])
    exact_df = df1[df1['title_norm'].isin(matched_titles)]

    if not exact_df.empty:
        out_df = exact_df.drop(columns=['title_norm'])
        print(":::::FINAL CSV INTERSECTION OUTPUT (EXACT):::::")
        print(out_df.to_csv(index=False))
        return out_df.to_csv(index=False)

    # ------------------------
    # 2️⃣ Fuzzy (if exact empty)
    # ------------------------
    results = []
    right_choices = df2['title_norm'].dropna().tolist()

    for _, left_row in df1.iterrows():
        left_key = left_row['title_norm']
        if not left_key:
            continue
        best = process.extractOne(left_key, right_choices, scorer=fuzz.token_sort_ratio)
        if best:
            match_title, score, _ = best
            if score >= threshold:
                results.append(left_row)

    if not results:
        return ""

    fuzzy_df = pd.DataFrame(results).drop(columns=['title_norm'], errors='ignore')

    print(":::::FINAL CSV INTERSECTION OUTPUT (FUZZY):::::")
    print(fuzzy_df.to_csv(index=False))

    return fuzzy_df.to_csv(index=False)
