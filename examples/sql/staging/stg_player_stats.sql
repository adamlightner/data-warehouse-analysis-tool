insert into {{ TARGET_TABLE }} (
    stat_id,
    game_id,
    player_id,
    passing_yards,
    rushing_yards,
    receiving_yards,
    touchdowns,
    interceptions,
    tackles,
    sacks
)
select
    upper(src.id) as stat_id,
    upper(src.game_id) as game_id,
    upper(src.player_id) as player_id,
    src.passing_yards,
    src.rushing_yards,
    src.receiving_yards,
    src.touchdowns,
    src.interceptions,
    src.tackles,
    src.sacks
from
    {{ SOURCE_TABLE }} src
;
