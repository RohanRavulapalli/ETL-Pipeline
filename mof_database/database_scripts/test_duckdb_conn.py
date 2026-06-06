import duckdb

conn = duckdb.connect('md:carbon_db')

conn.sql("SET memory_limit = '128GB'")

conn.sql("SELECT current_setting('memory_limit') AS memlimit;").show()

conn.close()
