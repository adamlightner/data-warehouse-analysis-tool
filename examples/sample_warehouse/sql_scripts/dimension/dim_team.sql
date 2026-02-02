merge into {{ TARGET_TABLE }} tgt 
using (
    select
        upper(s.id) as team_id,
        s.name as team_name,
        location,
        logo_url
    from
        {{ SOURCE_TABLE }} s
)
on tgt.id = s.id
when matched then
    set update
        tgt.team_name = s.team_name,
        tgt.location = s.location,
        tgt.logo_url = s.logo_url
when not matched
    insert (
        id, 
        team_name, 
        location, 
        logo_url
    )
    values (
        s.id, 
        s.team_name, 
        s.location, 
        s.logo_url
    )
;
