{{ config(materialized='view') }}

with source_data as (
    select * from {{ source('raw_weather', 'city_weather_optimized') }}
)

select
    date,
    city,
    country,
    avg_temp as temp_celsius,
    -- Simple Fahrenheit conversion for the dashboard
    round((avg_temp * 9/5) + 32, 2) as temp_fahrenheit
from source_data
where avg_temp is not null