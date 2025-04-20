import pandas as pd
import re
import ssl
import time
from tqdm import tqdm

ssl._create_default_https_context = ssl._create_unverified_context

def normalize_author(author):
    author = re.sub(r'\(.*?\)', '', author).strip()
    author = re.sub(r'\s+', ' ', author)
    if author.count(',') == 1:
        parts = [part.strip() for part in author.split(',', 1)]
        return f"{parts[1]} {parts[0]}"
    return author

def author_matches(author_field, query_lower):
    if query_lower in author_field.lower():
        return True

    authors = [a.strip() for a in re.split(r';|,', author_field) if a.strip()]
    query_normalized = normalize_author(query_lower).lower()
    query_parts = query_normalized.split()

    for author in authors:
        author_normalized = normalize_author(author).lower()
        author_parts = author_normalized.split()

        if query_normalized == author_normalized:
            return True
        if len(query_parts) == 1 and query_parts[0] in author_normalized:
            return True
        if len(query_parts) == 1 and any(part.startswith(query_parts[0]) for part in author_parts):
            return True
        if len(query_parts) == 2 and query_parts[::-1] == author_parts:
            return True

    return False

def matches(paper, key, query_lower):
    field_val = str(paper[key]).lower()
    return author_matches(field_val, query_lower) if key == 'Nama Penulis' else query_lower in field_val

def expand_matches(papers, start_idx, key, query_lower):
    results = [papers[start_idx]]

    i = start_idx - 1
    while i >= 0 and matches(papers[i], key, query_lower):
        results.append(papers[i])
        i -= 1

    i = start_idx + 1
    while i < len(papers) and matches(papers[i], key, query_lower):
        results.append(papers[i])
        i += 1

    return results

def binary_search(papers_sorted, key, query):
    left, right = 0, len(papers_sorted) - 1
    query_lower = query.lower()

    while left <= right:
        mid = (left + right) // 2
        if matches(papers_sorted[mid], key, query_lower):
            return expand_matches(papers_sorted, mid, key, query_lower)
        elif query_lower < str(papers_sorted[mid][key]).lower():
            right = mid - 1
        else:
            left = mid + 1
    return []

def linear_search(papers, key, query):
    query_lower = query.lower()
    return [paper for paper in papers if matches(paper, key, query_lower)]

def load_data():
    print("=== Data Source Selection ===")
    print("1. Load from online Google Sheet")
    print("2. Load from local Excel file")
    source_choice = input("Choose (1 or 2): ").strip()

    print("\nLoading data", end='')
    for _ in tqdm(range(10), desc="Progress", ncols=75):
        time.sleep(0.1)  # Simulate loading delay

    if source_choice == '1':
        url = "https://docs.google.com/spreadsheets/d/17ru4XAU2NloE9Dfxr2PC1BVcsYkLLT5r7nPSsiOFlvQ/export?format=csv&gid=743838712"
        try:
            df = pd.read_csv(url)
            print("✅ Successfully loaded online sheet!")
        except Exception as e:
            print(f"\n❌ Failed to load online sheet: {e}")
            return None
    else:
        try:
            df = pd.read_excel(r'masukkan_sumber_datasheet_offline_disini')
            print("✅ Successfully loaded local Excel file!")
        except FileNotFoundError:
            print("\n❌ Error: File not found. Check the path.")
            return None

    column_mapping = {
        'Judul Paper': 'Judul Paper',
        'Tahun Terbit': 'Tahun Terbit',
        'Nama Penulis': 'Nama Penulis',
        'Link Paper': 'Link Paper'
    }

    df = df.rename(columns=column_mapping)
    return df.to_dict('records')

def main():
    papers = load_data()
    if not papers:
        return

    while True:
        print("\n=== Choose Search Algorithm ===")
        print("1. Binary Search (faster for large datasets)")
        print("2. Linear Search (simpler, works for any dataset)")
        search_choice = input("Choose search algorithm (1-2): ").strip()

        if search_choice in ('1', '2'):
            break
        print("Invalid choice. Please enter 1 or 2.")

    use_binary = search_choice == '1'

    if use_binary:
        papers_sorted = {
            'Judul Paper': sorted(papers, key=lambda x: str(x['Judul Paper']).lower()),
            'Nama Penulis': sorted(papers, key=lambda x: str(x['Nama Penulis']).lower()),
            'Tahun Terbit': sorted(papers, key=lambda x: str(x['Tahun Terbit']))
        }
    else:
        papers_sorted = None

    while True:
        print("\n=== Research Paper Search ===")
        print("1. Search by Judul Paper")
        print("2. Search by Nama Penulis")
        print("3. Search by Tahun Terbit")
        print("4. Exit")

        choice = input("Choose (1-4): ").strip()
        if choice == '4':
            break

        query = input("Enter search query: ").strip()
        key_map = {'1': 'Judul Paper', '2': 'Nama Penulis', '3': 'Tahun Terbit'}
        key = key_map.get(choice)

        if not key:
            print("Invalid choice.")
            continue

        if use_binary and key != 'Nama Penulis':
            results = binary_search(papers_sorted[key], key, query)
        elif use_binary and key == 'Nama Penulis':
            results = binary_search(papers_sorted[key], key, query)
            if not results:
                results = linear_search(papers, key, query)
        else:
            results = linear_search(papers, key, query)

        if not results:
            print("No matches found.")
        else:
            print(f"\nFound {len(results)} papers:")
            for paper in results:
                print(f"\nJudul Paper: {paper['Judul Paper']}")
                print(f"Nama Penulis: {paper['Nama Penulis']}")
                print(f"Tahun Terbit: {paper['Tahun Terbit']}")
                print(f"Link Paper: {paper['Link Paper']}")

if __name__ == "__main__":
    main()
