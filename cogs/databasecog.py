import sqlalchemy
import sqlite3
from sqlite3 import Error
from discord.ext import commands
import cogs.cogbase as cogbase


class DatabaseCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

        # Connect to database
        self.database = r'database\server_database.db'
        self.connection = self.create_connection()

        # Create tables if not exist
        self.create_table(self.connection, "member", a=0)

    def create_connection(self):
        """ create a database connection to a SQLite database """
        conn = None
        try:
            conn = sqlite3.connect(self.database)
            # print(sqlite3.version)
        except Error as e:
            print(e)
        finally:
            return conn

    # no idea how to actually use it
    def close_connection(self):
        if self.connection:
            self.connection.close()
            print("[INFO]: Database connection closed")

    @staticmethod
    def create_table(conn, table_name: str, **kwargs):
        """ create a table from the create_table_sql statement
        :param table_name:
        :type table_name:
        :param conn: Connection object
        :return:
        """
        create_table_sql = f"""CREATE TABLE IF NOT EXISTS {table_name} (\n"""

        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)

    @staticmethod
    def create_project(conn, project):
        """
        Create a new project into the projects table
        :param conn:
        :param project:
        :return: project id
        """
        sql = ''' INSERT INTO projects(name,begin_date,end_date)
                      VALUES(?,?,?) '''
        cur = conn.cursor()
        cur.execute(sql, project)
        conn.commit()
        return cur.lastrowid

    @staticmethod
    def update_task(conn, task):
        """
        update priority, begin_date, and end date of a task
        :param conn:
        :param task:
        :return: project id
        """
        sql = ''' UPDATE tasks
                      SET priority = ? ,
                          begin_date = ? ,
                          end_date = ?
                      WHERE id = ?'''
        cur = conn.cursor()
        cur.execute(sql, task)
        conn.commit()

    @staticmethod
    def select_all_tasks(conn):
        """
        Query all rows in the tasks table
        :param conn: the Connection object
        :return:
        """
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks")

        rows = cur.fetchall()

        for row in rows:
            print(row)

    @staticmethod
    def delete_task(conn, where):
        """
        Delete a task by task id
        :param where:
        :param where: id of the task
        :param conn:  Connection to the SQLite database
        :return:
        """
        sql = 'DELETE FROM tasks WHERE id=?'
        cur = conn.cursor()
        cur.execute(sql, (where,))
        conn.commit()


def setup(bot: commands.Bot):
    bot.add_cog(DatabaseCog(bot))
