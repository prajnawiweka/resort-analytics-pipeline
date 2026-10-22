{#- Fails when the given columns together do not identify one row.
    Same idea as dbt_utils.unique_combination_of_columns, without the package dependency. -#}
{% test dbt_utils_free_unique_combination(model, columns) %}

select {{ columns | join(', ') }}, count(*) as rows_with_this_key
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1

{% endtest %}
