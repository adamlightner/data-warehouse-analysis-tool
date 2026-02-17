insert into {{ TARGET_TABLE }} (
    stat_id,
    game_id,
    game_date,
    player_id,
    player_name,
    team_id,
    team_name,
    position,
    passing_yards,
    rushing_yards,
    receiving_yards,
    touchdowns,
    interceptions,
    tackles,
    sacks
)
select
    ps.stat_id,
    ps.game_id,
    gm.game_date,
    ps.player_id,
    p.first_name || ' ' || p.last_name as player_name,
    p.team_id,
    p.team_name,
    p.position,
    ps.passing_yards,
    ps.rushing_yards,
    ps.receiving_yards,
    ps.touchdowns,
    ps.interceptions,
    ps.tackles,
    ps.sacks
from
    {{ SOURCE_TABLE }} ps
left join
    {{ PLAYER_TABLE }} p on ps.player_id = p.player_id
left join
    {{ GAME_TABLE }} gm on ps.game_id = gm.game_id
where
    gm.game_date > (select coalesce(max(game_date), '1900-01-01') from {{ TARGET_TABLE }})
;
