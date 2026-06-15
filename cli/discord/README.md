# Machine bridge (Discord)
1. In Discord: create a channel (e.g. #machine-bridge) -> Edit Channel -> Integrations
   -> Webhooks -> New Webhook -> Copy Webhook URL.
2. On EACH machine (desktop + laptop), in WSL:
     echo 'DISCORD_WEBHOOK=<paste-url>' > ~/Visual_Studio_Settings/cli/discord/.env
3. Test:  ~/Visual_Studio_Settings/cli/discord/notify.sh "desktop online"
Both machines + your phone now see each other's posts. (Acting on messages = the bot, next.)
