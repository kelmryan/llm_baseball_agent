# Kids username
THE_LORAX079
3l3chase

# get the photos
id=$(curl -X POST "https://users.roblox.com/v1/usernames/users"   -H "Content-Type: application/json"   -d '{
    "usernames": ["3l3chase"],
    "excludeBannedUsers": true
  }' | jq -r '.data[] | .id')

  id=$(curl -X POST "https://users.roblox.com/v1/usernames/users"   -H "Content-Type: application/json"   -d '{
    "usernames": ["3l3chase"],
    "excludeBannedUsers": true
  }' | jq -r '.data[] | .id')

- got id from above
- Then run   
  photo=$(curl "https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds=$id&size=420x420&format=Png" | jq -r '.data[] | .imageUrl' )
- Get the imageUrl
- Then run
  curl -o "3l3chase.png" $photo