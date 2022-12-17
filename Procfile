user: hypercorn user --reload --debug --bind wordle.local.gd:$PORT --access-logfile - --error-logfile - --log-level DEBUG

game_s1: ./bin/litefs -config ./etc/primary.yml
game_s2: ./bin/litefs -config ./etc/secondary1.yml
game_s3: ./bin/litefs -config ./etc/secondary2.yml

leaderboard: hypercorn leaderboard --reload --debug --bind wordle.local.gd:$PORT --access-logfile - --error-logfile - --log-level DEBUG

