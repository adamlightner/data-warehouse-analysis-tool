insert into {{ TARGET_TABLE }} tgt (
    game_id,
    game_date,
    home_team_id,
    home_score,
    vis_team_id,
    vis_score
)
select
    upper(src.id) as game_id,
    timestamp(src.game_time) as game_date,
    upper(src.home_team) as home_team_id,
    src.home_score,
    upper(src.vis_team) as vis_team_id,
    src.vis_score
from
    {{ SOURCE_TABLE }} src
;
