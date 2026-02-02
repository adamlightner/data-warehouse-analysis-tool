insert into {{ TARGET_TABLE }} tgt (
    game_id,
    game_date,
    home_team_id,
    home_team_name,
    home_score,
    vis_team_id,
    vis_team_name,
    vis_score
)
select
    gm.game_id,
    gm.game_date,
    gm.home_team_id,
    home_t.team_name as home_team_name,
    gm.home_score,
    gm.vis_team_id,
    vis_t.team_name as vis_team_name,
    gm.vis_score
from
    {{ GAME_TABLE }} gm
left join 
    {{ TEAM_TABLE }} as home_t on upper(src.home_team) = home_t.team_id
left join 
    {{ TEAM_TABLE }} as vis_t on upper(src.vis_team) = vis_t.team_id
where
    gm.game_date > (select max(game_date) from {{ GAME_TABLE }})
;
