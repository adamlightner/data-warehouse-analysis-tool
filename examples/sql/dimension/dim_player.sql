merge into {{ TARGET_TABLE }} tgt
using (
    select
        p.player_id,
        p.first_name,
        p.last_name,
        p.team_id,
        t.team_name,
        p.position,
        p.jersey_number
    from
        {{ SOURCE_TABLE }} p
    left join
        {{ TEAM_TABLE }} t on p.team_id = t.team_id
) src
on tgt.player_id = src.player_id
when matched then
    update set
        tgt.first_name = src.first_name,
        tgt.last_name = src.last_name,
        tgt.team_id = src.team_id,
        tgt.team_name = src.team_name,
        tgt.position = src.position,
        tgt.jersey_number = src.jersey_number
when not matched then
    insert (
        player_id,
        first_name,
        last_name,
        team_id,
        team_name,
        position,
        jersey_number
    )
    values (
        src.player_id,
        src.first_name,
        src.last_name,
        src.team_id,
        src.team_name,
        src.position,
        src.jersey_number
    )
;
