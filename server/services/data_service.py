"""
数据服务
提供数据库访问和书籍数据管理功能
"""
import os
import json
import tempfile
from typing import Optional, Dict, List, Any

# 数据库连接
import snowflake.connector

# 文件路径工具函数
from utils.file_utils import ensure_directory_exists

class DataService:
    """
    数据服务类

    处理数据库连接、书籍数据获取和缓存管理。

    属性:
        conn: 数据库连接对象
        cache_dir: 缓存目录
    """

    def __init__(self,
                snowflake_user: Optional[str] = None,
                snowflake_password: Optional[str] = None,
                snowflake_account: Optional[str] = None,
                cache_dir: Optional[str] = None):
        """
        初始化数据服务

        参数:
            snowflake_user (Optional[str]): Snowflake用户名，默认从环境变量获取
            snowflake_password (Optional[str]): Snowflake密码，默认从环境变量获取
            snowflake_account (Optional[str]): Snowflake账户，默认从环境变量获取
            cache_dir (Optional[str]): 缓存目录路径，默认为项目根目录下的cache目录

        示例:
            >>> service = DataService()  # 使用环境变量中的配置
            >>> service = DataService(snowflake_user="user", snowflake_password="pass", snowflake_account="acct")  # 自定义配置
        """
        self.conn = None
        self.snowflake_user = snowflake_user or os.getenv("SNOWFLAKE_USER")
        self.snowflake_password = snowflake_password or os.getenv("SNOWFLAKE_PASSWORD")
        self.snowflake_account = snowflake_account or os.getenv("SNOWFLAKE_ACCOUNT")

        # 设置缓存目录
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            # 默认缓存目录在项目根目录下的cache目录
            self.cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "cache")
            ensure_directory_exists(self.cache_dir)

    def get_db_connection(self):
        """
        获取数据库连接，如果不存在则创建新连接

        返回:
            数据库连接对象

        示例:
            >>> conn = data_service.get_db_connection()
            >>> cursor = conn.cursor()
        """
        if self.conn is None:
            self.conn = snowflake.connector.connect(
                user=self.snowflake_user,
                password=self.snowflake_password,
                account=self.snowflake_account
            )
        return self.conn

    def close_db_connection(self):
        """
        关闭数据库连接

        示例:
            >>> data_service.close_db_connection()
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def fetch_book_content(self, book_id: str) -> Optional[Dict[str, Any]]:
        """
        根据书籍ID获取书籍内容

        参数:
            book_id (str): 书籍ID

        返回:
            Optional[Dict[str, Any]]: 包含书籍ID、标题、描述和内容的字典，如果未找到则返回None

        示例:
            >>> book = data_service.fetch_book_content("12345-1")
            >>> if book:
            >>>     print(f"Book title: {book['book_title']}")
        """
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
        print(f"📊 获取书籍内容: {book_id}")

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()

            if not rows:
                return None

            # 解析扩展信息获取书籍内容
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

        except Exception as e:
            print(f"⚠️ 获取书籍内容错误: {str(e)}")
            return None

    def fetch_all_production_books(self) -> str:
        """
        获取所有生产环境中的书籍信息，并缓存到文件中

        返回:
            str: 缓存文件路径

        示例:
            >>> cache_file = data_service.fetch_all_production_books()
            >>> print(f"书籍数据已缓存到: {cache_file}")
        """
        # 检查缓存文件是否存在
        cache_file = os.path.join(self.cache_dir, "production_books.json")
        if os.path.exists(cache_file):
            print(f"📚 使用缓存的书籍数据: {cache_file}")
            return cache_file

        print("📊 获取所有生产环境中的书籍...")

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            sql = """
            SELECT distinct PERMANENT_ID, TITLE, DESCRIPTION
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

            # 将数据转换为JSON格式
            library_data = ""
            for row in rows:
                json_data = {
                    "book_id": row[0],
                    "book_title": row[1],
                    "book_Description": row[2]
                }
                library_data += json.dumps(json_data) + "\n"

            # 创建临时文件并写入数据
            ensure_directory_exists(self.cache_dir)
            with open(cache_file, 'w') as f:
                f.write(library_data)

            print(f"✅ 书籍数据已保存到: {cache_file}")
            return cache_file

        except Exception as e:
            print(f"⚠️ 获取书籍数据错误: {str(e)}")

            # 如果出错，创建一个空的缓存文件作为备用
            with open(cache_file, 'w') as f:
                f.write("")

            return cache_file

    def search_books_by_title(self, title: str) -> List[Dict[str, Any]]:
        """
        根据标题搜索书籍

        参数:
            title (str): 书籍标题关键词

        返回:
            List[Dict[str, Any]]: 匹配的书籍列表

        示例:
            >>> books = data_service.search_books_by_title("Adventure")
            >>> print(f"找到 {len(books)} 本匹配的书籍")
        """
        sql = f"""
        SELECT distinct PERMANENT_ID, TITLE, DESCRIPTION
        FROM FIVETRAN_DATABASE.PICKATALE_STUDIO_PROD_PUBLIC.REGULAR_BOOK RB
                INNER JOIN FIVETRAN_DATABASE.PICKATALE_STUDIO_PROD_PUBLIC.PUBLISHED_BOOK PB ON PB.PUBLISHED_BOOK_ID = RB.ID
                INNER JOIN FIVETRAN_DATABASE.PICKATALE_STUDIO_PROD_PUBLIC.PUBLISHED_BOOK_ENVIRONMENTS PBE
                        ON PBE.PUBLISHED_BOOK_ID = PB.ID
                INNER JOIN FIVETRAN_DATABASE.PICKATALE_STUDIO_PROD_PUBLIC.ENVIRONMENT E
                        ON E.ID = PBE.ENVIRONMENTS_ID
            AND E.NAME = 'production'
            AND UPPER(RB.TITLE) LIKE UPPER('%{title}%');
        """

        print(f"📊 搜索书籍标题: {title}")

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()

            results = []
            for row in rows:
                results.append({
                    "book_id": row[0],
                    "book_title": row[1],
                    "book_Description": row[2]
                })

            return results

        except Exception as e:
            print(f"⚠️ 搜索书籍错误: {str(e)}")
            return []
