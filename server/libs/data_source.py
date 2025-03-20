import snowflake.connector
import json
import os, sys
import tempfile

# load db settings from dotenv
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(__file__))
import prompt_templates as pt

conn = None
def get_db_connection():
  global conn
  if conn is None:
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT")

    )
  return conn

def close_db_connection():
  global conn
  if conn is not None:
    conn.close()
    conn = None
  return


def fetch_book_content(book_id):
  sql = f"""
SELECT distinct PERMANENT_ID, TITLE, DESCRIPTION, EXTENDED_BOOK_INFO
FROM FIVETRAN_DATABASE.PICKATALE_STUDIO_PROD_PUBLIC.REGULAR_BOOK RB
         INNER JOIN FIVETRAN_DATABASE.PICKATALE_STUDIO_PROD_PUBLIC.PUBLISHED_BOOK PB ON PB.PUBLISHED_BOOK_ID = RB.ID
         INNER JOIN FIVETRAN_DATABASE.PICKATALE_STUDIO_PROD_PUBLIC.PUBLISHED_BOOK_ENVIRONMENTS PBE
                    ON PBE.PUBLISHED_BOOK_ID = PB.ID
         INNER JOIN FIVETRAN_DATABASE.PICKATALE_STUDIO_PROD_PUBLIC.ENVIRONMENT E
                    ON E.ID = PBE.ENVIRONMENTS_ID
         INNER JOIN FIVETRAN_DATABASE.PICKATALE_STUDIO_PROD_PUBLIC.BOOK_EXTENDED_INFO BEI on BEI.BOOK_ID = RB.ID
    AND E.NAME = 'production'
    AND RB.PERMANENT_ID = '{book_id}';
  """
  print("📊 Fetching book content...")
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(sql)
  rows = cursor.fetchall()
  cursor.close()
  if len(rows) == 0:
    return None
  else:
    extended_info = json.loads(rows[0][3])
    book_content = ""
    for page in extended_info:
      book_content += page["rawText"] + "\n"

    return {
      "book_id": rows[0][0],
      "book_title": rows[0][1],
      "book_description": rows[0][2],
      "book_content": book_content
    }


def fetch_all_production_books():
  """
  从数据库中获取所有的图书信息，并返回一个临时文件的路径
  """
  # cache file should locate in the project_root/cache folder
  cache_file = os.path.join(os.path.dirname(__file__), "..", "..", "cache", "production_books.json")
  if os.path.exists(cache_file):
    return cache_file

  print("📊 Fetching all production books...")
  conn = get_db_connection()
  cursor = conn.cursor()
  sql = f"""
  SELECT distinct PERMANENT_ID, TITLE, DESCRIPTION,
  FROM FIVETRAN_DATABASE.PICKATALE_STUDIO_PROD_PUBLIC.REGULAR_BOOK RB
         INNER JOIN FIVETRAN_DATABASE.PICKATALE_STUDIO_PROD_PUBLIC.PUBLISHED_BOOK PB ON PB.PUBLISHED_BOOK_ID = RB.ID
         INNER JOIN FIVETRAN_DATABASE.PICKATALE_STUDIO_PROD_PUBLIC.PUBLISHED_BOOK_ENVIRONMENTS PBE
                    ON PBE.PUBLISHED_BOOK_ID = PB.ID
         INNER JOIN FIVETRAN_DATABASE.PICKATALE_STUDIO_PROD_PUBLIC.ENVIRONMENT E
                    ON E.ID = PBE.ENVIRONMENTS_ID
    AND E.NAME = 'production';
  """
  cursor.execute(sql)
  rows = cursor.fetchall()
  cursor.close()
  library_data = ""
  for row in rows:
    json_data = {
      "book_id": row[0],
      "book_title": row[1],
      "book_Description": row[2]
    }
    library_data += json.dumps(json_data) + "\n"
  # 使用python的函数在系统的临时文件目录中，创建一个临时文件，把书籍信息写入并返回这个临时文件的路径
  # 并使用.txt作为文件的后缀
  temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
  temp_file.write(library_data)
  temp_file.close()
  #move the file to the project root/data folder
  os.rename(temp_file.name, cache_file)
  return cache_file