create or replace view {{ TARGET_VIEW }} as
select
    t.team_id,
    t.team_name,
    t.location,
    count(case when gm.home_team_id = t.team_id and gm.home_score > gm.vis_score then 1
               when gm.vis_team_id = t.team_id and gm.vis_score > gm.home_score then 1 end) as wins,
    count(case when gm.home_team_id = t.team_id and gm.home_score < gm.vis_score then 1
               when gm.vis_team_id = t.team_id and gm.vis_score < gm.home_score then 1 end) as losses,
    count(case when (gm.home_team_id = t.team_id or gm.vis_team_id = t.team_id)
                and gm.home_score = gm.vis_score then 1 end) as ties,
    sum(case when gm.home_team_id = t.team_id then gm.home_score
             when gm.vis_team_id = t.team_id then gm.vis_score else 0 end) as points_for,
    sum(case when gm.home_team_id = t.team_id then gm.vis_score
             when gm.vis_team_id = t.team_id then gm.home_score else 0 end) as points_against
from
    {{ TEAM_TABLE }} t
left join
    {{ GAME_TABLE }} gm on t.team_id = gm.home_team_id or t.team_id = gm.vis_team_id
group by
    t.team_id,
    t.team_name,
    t.location
;
