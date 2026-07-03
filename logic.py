import sqlite3
from config import DATABASE


skills = [(_,) for _ in ['Python', 'SQL', 'API', 'Discord']]

statuses = [(_,) for _ in [
    'Prototip Oluşturma',
    'Geliştirme Aşamasında',
    'Tamamlandı, kullanıma hazır',
    'Güncellendi',
    'Tamamlandı, ancak bakımı yapılmadı'
]]


class DB_Manager:
    def __init__(self, database):
        self.database = database

    def __connect(self):
        conn = sqlite3.connect(self.database)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_tables(self):
        conn = self.__connect()

        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS status (
                    status_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status_name TEXT UNIQUE NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT UNIQUE NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    project_name TEXT NOT NULL,
                    description TEXT,
                    url TEXT,
                    status_id INTEGER,
                    FOREIGN KEY(status_id) REFERENCES status(status_id),
                    UNIQUE(user_id, project_name)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS project_skills (
                    project_id INTEGER NOT NULL,
                    skill_id INTEGER NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                    FOREIGN KEY(skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
                    UNIQUE(project_id, skill_id)
                )
            """)

        conn.close()

    def __execute(self, sql, data=tuple()):
        conn = self.__connect()

        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            conn.commit()

        conn.close()

    def __executemany(self, sql, data):
        conn = self.__connect()

        with conn:
            conn.executemany(sql, data)
            conn.commit()

        conn.close()

    def __select_data(self, sql, data=tuple()):
        conn = self.__connect()

        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            result = cur.fetchall()

        conn.close()
        return result

    def default_insert(self):
        sql = 'INSERT OR IGNORE INTO skills (skill_name) VALUES (?)'
        self.__executemany(sql, skills)

        sql = 'INSERT OR IGNORE INTO status (status_name) VALUES (?)'
        self.__executemany(sql, statuses)

    def insert_project(self, data):
        sql = """
            INSERT OR IGNORE INTO projects 
            (user_id, project_name, description, url, status_id) 
            VALUES (?, ?, ?, ?, ?)
        """
        self.__execute(sql, data)

    def insert_skill(self, user_id, project_name, skill):
        project_id = self.get_project_id(project_name, user_id)

        if project_id is None:
            raise ValueError("Proje bulunamadı!")

        sql = 'SELECT skill_id FROM skills WHERE skill_name = ?'
        skill_result = self.__select_data(sql, (skill,))

        if not skill_result:
            raise ValueError("Skill bulunamadı!")

        skill_id = skill_result[0][0]

        sql = 'INSERT OR IGNORE INTO project_skills (project_id, skill_id) VALUES (?, ?)'
        self.__execute(sql, (project_id, skill_id))

    def get_statuses(self):
        sql = "SELECT status_name FROM status"
        return self.__select_data(sql)

    def get_status_id(self, status_name):
        sql = 'SELECT status_id FROM status WHERE status_name = ?'
        result = self.__select_data(sql, (status_name,))

        if result:
            return result[0][0]

        return None

    def get_projects(self, user_id):
        sql = """
            SELECT 
                projects.project_id,
                projects.project_name,
                projects.description,
                projects.url,
                status.status_name
            FROM projects
            LEFT JOIN status ON status.status_id = projects.status_id
            WHERE projects.user_id = ?
        """
        return self.__select_data(sql, (user_id,))

    def get_project_id(self, project_name, user_id):
        sql = """
            SELECT project_id 
            FROM projects 
            WHERE project_name = ? AND user_id = ?
        """
        result = self.__select_data(sql, (project_name, user_id))

        if result:
            return result[0][0]

        return None

    def get_skills(self):
        sql = 'SELECT * FROM skills'
        return self.__select_data(sql)

    def get_project_skills(self, user_id, project_name):
        sql = """
            SELECT skills.skill_name 
            FROM projects 
            JOIN project_skills ON projects.project_id = project_skills.project_id 
            JOIN skills ON skills.skill_id = project_skills.skill_id 
            WHERE projects.project_name = ? AND projects.user_id = ?
        """
        result = self.__select_data(sql, (project_name, user_id))
        return ', '.join([x[0] for x in result])

    def get_project_info(self, user_id, project_name):
        sql = """
            SELECT 
                projects.project_name, 
                projects.description, 
                projects.url, 
                status.status_name 
            FROM projects 
            LEFT JOIN status ON status.status_id = projects.status_id
            WHERE projects.project_name = ? AND projects.user_id = ?
        """
        return self.__select_data(sql, (project_name, user_id))

    def update_project(self, param, data):
        allowed_params = ['project_name', 'description', 'url', 'status_id']

        if param not in allowed_params:
            raise ValueError("Geçersiz parametre!")

        sql = f"""
            UPDATE projects 
            SET {param} = ? 
            WHERE project_name = ? AND user_id = ?
        """
        self.__execute(sql, data)

    def delete_project(self, user_id, project_id):
        sql = """
            DELETE FROM projects 
            WHERE user_id = ? AND project_id = ?
        """
        self.__execute(sql, (user_id, project_id))

    def delete_skill(self, project_id, skill_id):
        sql = """
            DELETE FROM project_skills
            WHERE project_id = ? AND skill_id = ?
        """
        self.__execute(sql, (project_id, skill_id))

    def add_column_if_not_exists(self, table_name, column_name, column_type):
        sql = f"PRAGMA table_info({table_name})"
        columns = self.__select_data(sql)

        existing_columns = [column[1] for column in columns]

        if column_name not in existing_columns:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            self.__execute(sql)
            return True

        return False


if __name__ == '__main__':
    manager = DB_Manager(DATABASE)

    manager.create_tables()
    manager.default_insert()

    print("Tablolar oluşturuldu ve varsayılan veriler eklendi.")