{{ config(materialized='view') }}

with source_data as (
    select * from {{ source('raw_weather', 'city_weather_optimized') }}
),

deduplicated as (
    select 
        *,
        -- Groups identical rows and assigns a number to each
        row_number() over (
            partition by date, city, country 
            order by date
        ) as row_num
    from source_data
)

select
    date,
    city,
    country,
    avg_temp as temp_celsius,
    round((avg_temp * 9/5) + 32, 2) as temp_fahrenheit
from deduplicated
-- Only keep the first occurrence of each row
-- BigQuery Power Move: Deduplicate directly in the final select
qualify row_number() over (
    partition by date, city, country 
    order by date
) = 1