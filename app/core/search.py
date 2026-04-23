from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import sqlite3

async def setup_fts(db: AsyncSession):
    """
    Setup SQLite FTS5 for products.
    """
    # Create the FTS5 virtual table
    await db.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS products_search USING fts5(
            name,
            description,
            content='products',
            content_rowid='id'
        );
    """))

    # Create triggers to keep FTS table in sync
    await db.execute(text("""
        CREATE TRIGGER IF NOT EXISTS products_ai AFTER INSERT ON products BEGIN
          INSERT INTO products_search(rowid, name, description) VALUES (new.id, new.name, new.description);
        END;
    """))

    await db.execute(text("""
        CREATE TRIGGER IF NOT EXISTS products_ad AFTER DELETE ON products BEGIN
          INSERT INTO products_search(products_search, rowid, name, description) VALUES('delete', old.id, old.name, old.description);
        END;
    """))

    await db.execute(text("""
        CREATE TRIGGER IF NOT EXISTS products_au AFTER UPDATE ON products BEGIN
          INSERT INTO products_search(products_search, rowid, name, description) VALUES('delete', old.id, old.name, old.description);
          INSERT INTO products_search(rowid, name, description) VALUES (new.id, new.name, new.description);
        END;
    """))

    # Initial sync
    await db.execute(text("""
        INSERT OR IGNORE INTO products_search(rowid, name, description)
        SELECT id, name, description FROM products;
    """))

    await db.commit()

async def fuzzy_search_products(db: AsyncSession, query_str: str, limit: int = 20):
    """
    Perform a fuzzy search using SQLite FTS5.
    """
    # FTS5 doesn't have native "fuzzy" like Levenshtein, but we can use:
    # 1. Prefix matching (term*)
    # 2. Ranking (bm25)
    # 3. Near operator

    # Sanitize and prepare query
    terms = [f"{term}*" for term in query_str.split() if term]
    fts_query = " ".join(terms)

    sql = text("""
        SELECT p.*, bm25(products_search) as rank
        FROM products p
        JOIN products_search ps ON p.id = ps.rowid
        WHERE products_search MATCH :query
        ORDER BY rank
        LIMIT :limit
    """)

    result = await db.execute(sql, {"query": fts_query, "limit": limit})
    return result.mappings().all()
