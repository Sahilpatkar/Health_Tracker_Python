select food_id,date,F1.meal_type,F1.food_item,quantity,serving_size,protein,fat,
from food_intake F1
join food_items F2 on F1.food_id = F2.id;



with user_table as (
    select * from food_intake
             where user = "sahil"
)

select date,F1.meal_type, SUM(quantity*protein) as total_protein_per_meal, SUM(quantity*fat) as total_fat_per_meal, SUM(quantity*calories) as total_calories_per_meal
from user_table F1
join food_items F2 on F1.food_id = F2.id
group by date,F1.meal_type;



with user_table as (
    select * from food_intake
             where user = "sahil"
)

select date, SUM(total_protein_per_meal) as total_protein_per_day, SUM(total_fat_per_meal) as total_fat_per_day, SUM(total_calories_per_meal) as total_calories_per_day
from(select date,F1.meal_type, SUM(quantity*protein) as total_protein_per_meal, SUM(quantity*fat) as total_fat_per_meal, SUM(quantity*calories) as total_calories_per_meal
from user_table F1
join food_items F2 on F1.food_id = F2.id
group by date,F1.meal_type) table1
group by date;