# Make blueprints

The JSON files are standalone native Make templates exported from the public TechMouad planner:

- `wordpress-telegram.make-blueprint.json`: published post title + link to Telegram.
- `rss-telegram.make-blueprint.json`: feed item title + link to Telegram.
- `sheets-wordpress.make-blueprint.json`: approved row to a **draft**, then write its ID back.

Import into a new inactive scenario. Select your own connections and the same suitable Data store in modules 2, 3 and 5. Use Text fields `state`, `destination_id` and Date `updated_at`. Keep overwrite disabled in module 3 and insert-missing disabled in module 5. Do not skip reservation errors. Configure watcher start points and schedule in Make; these are not transferred by the files.

Sheets uses a `Content` tab with A:E = `item_id,title,content,status,post_id`, status `ready`, empty post_id, native column range A-Z, and RAW writeback. Do not reorder rows during execution. Post status is explicitly `draft`.

Run once with one test item. Review destination and receipt before retrying uncertain outcomes; these templates do not promise exactly-once delivery. The original connected tests used five modules for each Telegram path and six for Sheets. Your own connections and permissions still need testing.

Planner and Arabic instructions: https://techmouad.com/automation-workflow-planner/
