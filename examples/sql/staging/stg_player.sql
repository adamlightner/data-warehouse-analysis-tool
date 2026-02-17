insert into {{ TARGET_TABLE }} (
    player_id,
    first_name,
    last_name,
    team_id,
    position,
    jersey_number
)
select
    upper(src.id) as player_id,
    src.first_name,
    src.last_name,
    upper(src.team_id) as team_id,
    src.position,
    src.jersey_number
from
    {{ SOURCE_TABLE }} src
;
