#!/bin/bash
username=${1:-"3l3chase"}
main() {
   id=$(curl -X POST "https://users.roblox.com/v1/usernames/users" \
  -H "Content-Type: application/json" \
  -d "{\"usernames\": [\"$username\"], \"excludeBannedUsers\": true}" |
  jq -r '.data[] | .id')

  photo=$(curl "https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds=$id&size=420x420&format=Png" | jq -r '.data[] | .imageUrl' )

  curl -o "$username.png" $photo
}

main "$@"