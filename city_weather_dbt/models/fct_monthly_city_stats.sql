{{ config(
    materialized='table',
    partition_by={
      "field": "month_start_date",
      "data_type": "date",
      "granularity": "month"
    },
    cluster_by=["country", "city"]
) }}

with staged_data as (
    select * from {{ ref('stg_weather') }} -- References the Silver model
)

select
    -- Truncates the timestamp to the first day of the month
    date_trunc(date, month) as month_start_date,
    city,
    country,
    -- Aggregated Metrics
    round(avg(temp_celsius), 2) as monthly_avg_temp_c,
    round(avg(temp_fahrenheit), 2) as monthly_avg_temp_f,
    min(temp_celsius) as min_temp_c,
    max(temp_celsius) as max_temp_c,
    count(*) as days_recorded
from staged_data
group by 1, 2, 3