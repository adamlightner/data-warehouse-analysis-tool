merge into {{ TARGET_TABLE }} tgt 
using (
    select
        upper(s.id) as team_id,
        s.name as team_name,
        location,
        logo_url
    from
        {{ SOURCE_TABLE }} s
) src
on tgt.team_id = src.team_id
when matched then
    update set
        tgt.team_name = src.team_name,
        tgt.location = src.location,
        tgt.logo_url = src.logo_url
when not matched
    insert (
        team_id, 
        team_name, 
        location, 
        logo_url
    )
    values (
        src.id, 
        src.team_name, 
        src.location, 
        src.logo_url
    )
;
