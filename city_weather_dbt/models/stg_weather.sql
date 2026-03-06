{{ config(materialized='view') }}

with source_data as (
    -- 1. Get the raw data
    select * from {{ source('raw_weather', 'city_weather_optimized') }}
)

select
    date,
    city,
    country,
    avg_temp as temp_celsius,
    round((avg_temp * 9/5) + 32, 2) as temp_fahrenheit
from source_data
-- 2. Filter out the null rows
where date is not null 
  and city is not null
-- 3. Deduplicate in one step
qualify row_number() over (
    partition by date, city, country 
    order by date
) = 1