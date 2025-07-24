import mysql.connector

def create_mysql_table_if_not_exists():
    conn = mysql.connector.connect(
        host="localhost",     # or your Docker host/service name
        user="youruser",
        password="yourpass",
        database="health"
    )
    cursor = conn.cursor()

    create_query = """
    CREATE TABLE IF NOT EXISTS health_parameters (
        user VARCHAR(100),
        patient_name VARCHAR(100),
        report_date VARCHAR(30),
        gender VARCHAR(10),
        location TEXT,
        parameter_name TEXT,
        value TEXT,
        unit TEXT,
        remark TEXT
    );
    """
    cursor.execute(create_query)
    conn.commit()
    print("✅ MySQL table 'health_parameters' is ready.")
    cursor.close()
    conn.close()
