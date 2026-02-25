"""Compare schema of two SQLite DBs: pre-merge copy vs post-merge."""
import sqlite3
import sys

def get_schema(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    info = {}
    for t in tables:
        cur = conn.execute(f'PRAGMA table_info("{t}")')
        info[t] = cur.fetchall()
    conn.close()
    return tables, info

def main():
    pre = "aiwebtest.db.pre-merge"
    post = "aiwebtest.db"
    pre_t, pre_info = get_schema(pre)
    post_t, post_info = get_schema(post)

    print("=== TABLES ===")
    print("Pre-merge:", sorted(pre_t))
    print("Post-merge:", sorted(post_t))
    only_pre = set(pre_t) - set(post_t)
    only_post = set(post_t) - set(pre_t)
    if only_pre:
        print("Only in PRE-MERGE:", only_pre)
    if only_post:
        print("Only in POST-MERGE:", only_post)
    print()

    print("=== TABLE STRUCTURE (columns) ===")
    all_tables = sorted(set(pre_t) | set(post_t))
    for t in all_tables:
        pre_cols = pre_info.get(t, [])
        post_cols = post_info.get(t, [])
        pre_names = [c[1] for c in pre_cols]
        post_names = [c[1] for c in post_cols]
        if pre_cols != post_cols:
            print(f"--- {t} ---")
            print("  Pre-merge columns:", pre_names)
            print("  Post-merge columns:", post_names)
            if pre_names != post_names:
                only_pre_cols = set(pre_names) - set(post_names)
                only_post_cols = set(post_names) - set(pre_names)
                if only_pre_cols:
                    print("  Only in PRE:", only_pre_cols)
                if only_post_cols:
                    print("  Only in POST:", only_post_cols)
        else:
            print(f"{t}: same structure")
    print()

    # Indexes
    print("=== INDEXES ===")
    for label, path in [("Pre-merge", pre), ("Post-merge", post)]:
        conn = sqlite3.connect(path)
        cur = conn.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY tbl_name, name")
        idx = cur.fetchall()
        conn.close()
        print(f"{label}: {idx}")

def row_counts(path):
    conn = sqlite3.connect(path)
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [r[0] for r in cur.fetchall()]
    counts = {}
    for t in tables:
        cur = conn.execute(f'SELECT COUNT(*) FROM "{t}"')
        counts[t] = cur.fetchone()[0]
    conn.close()
    return counts

if __name__ == "__main__":
    main()
    print("=== ROW COUNTS ===")
    pre_counts = row_counts("aiwebtest.db.pre-merge")
    post_counts = row_counts("aiwebtest.db")
    for t in sorted(pre_counts.keys()):
        pre_n, post_n = pre_counts[t], post_counts.get(t, 0)
        diff = post_n - pre_n
        if diff != 0:
            print(f"  {t}: pre={pre_n} post={post_n} (diff={diff:+d})")
    if pre_counts == post_counts:
        print("  (all tables have same row counts)")
