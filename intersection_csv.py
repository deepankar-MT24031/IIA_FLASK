from io import StringIO
import pandas as pd
import re
import unicodedata
from rapidfuzz import process, fuzz

def find_csv_intersection_from_strings(csv_str1: str,
                                       csv_str2: str,
                                       threshold: int = 85) -> str:
    """
    Take two CSVs as strings, return intersection as a CSV string.
    - Performs normalized exact match first.
    - If exact returns zero rows, performs fuzzy matching with given threshold.
    - Returns CSV string (empty string if no matches found).
    """

    # --- helper: normalize titles ---
    def normalize_title(s):
        if pd.isna(s):
            return ''
        s = str(s)
        # normalize unicode and drop diacritics / weird encodings
        s = unicodedata.normalize('NFKD', s)
        s = s.encode('ascii', 'ignore').decode('ascii')
        # remove punctuation, collapse whitespace, lowercase
        s = re.sub(r'[^\w\s]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip().lower()
        # optional: strip leading "the "
        if s.startswith('the '):
            s = s[4:]
        return s

    # --- read CSV strings into DataFrames (robust to leading spaces in headers) ---
    df1 = pd.read_csv(StringIO(csv_str1), skipinitialspace=True, dtype=str)
    df2 = pd.read_csv(StringIO(csv_str2), skipinitialspace=True, dtype=str)

    # ensure 'title' column exists
    if 'title' not in df1.columns or 'title' not in df2.columns:
        raise ValueError("Both CSV inputs must contain a 'title' column.")

    # add normalized title column
    df1 = df1.copy()
    df2 = df2.copy()
    df1['title_norm'] = df1['title'].map(normalize_title)
    df2['title_norm'] = df2['title'].map(normalize_title)

    # ------------------------
    # 1) Exact (normalized) match
    # ------------------------
    exact = df1.merge(df2, on='title_norm', how='inner', suffixes=('_csv1', '_csv2'))
    if not exact.empty:
        # drop the normalized helper column for output (optional)
        out_df = exact.drop(columns=['title_norm'])
        return out_df.to_csv(index=False)

    # ------------------------
    # 2) Fuzzy match (only if exact returned no rows)
    # ------------------------
    results = []
    right_choices = df2['title_norm'].tolist()

    # build a mapping from normalized title to rows (to handle duplicates)
    right_map = {}
    for idx, row in df2.iterrows():
        key = row['title_norm']
        right_map.setdefault(key, []).append((idx, row))

    for _, left_row in df1.iterrows():
        left_key = left_row['title_norm']
        if not left_key:
            continue
        best = process.extractOne(left_key, right_choices, scorer=fuzz.token_sort_ratio)
        if best:
            match_title, score, _ = best
            if score >= threshold:
                # for each matching right-row with that normalized title, create merged row
                for (_, right_row) in right_map.get(match_title, []):
                    # combine into a single Series with suffixes to avoid column name collision
                    combined = {}
                    for c in df1.columns:
                        combined[f"{c}_csv1"] = left_row.get(c)
                    for c in df2.columns:
                        combined[f"{c}_csv2"] = right_row.get(c)
                    combined['match_score'] = score
                    results.append(combined)

    if not results:
        # nothing matched
        return ""

    fuzzy_df = pd.DataFrame(results)
    # remove the helper norm columns from fuzzy_df if present duplicated
    cols_to_drop = [c for c in fuzzy_df.columns if c.endswith('_csv1') and c.startswith('title_norm')]
    cols_to_drop += [c for c in fuzzy_df.columns if c.endswith('_csv2') and c.startswith('title_norm')]
    fuzzy_df = fuzzy_df.drop(columns=cols_to_drop, errors='ignore')

    return fuzzy_df.to_csv(index=False)
