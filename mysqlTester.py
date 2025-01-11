import mysql.connector
import pandas as pd
import openpyxl

food_info = pd.read_excel("food_items.xlsx")

mydb = mysql.connector.connect(
  host="localhost",
  port="3305",
  user="root",
  password="123456"
)

# mycursor = mydb.cursor()

# mycursor.execute("use healthtracker;")

# mycursor.execute("show tables;")

# mycursor.execute("select * from food_items;")

#mycursor.execute("Insert into food_items values()")


for x in mycursor:
  print(x)

print(food_info)