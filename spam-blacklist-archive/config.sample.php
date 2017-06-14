<?php

$C["wikiapi"] = "https://zh.wikipedia.org/w/api.php";
$C["user"] = "";
$C["pass"] = "";

$C["from_page"] = "MediaWiki_talk:Spam-blacklist";
$C["to_page_prefix"] = "MediaWiki_talk:Spam-blacklist/存档/";

$C["retention_time"] = "https://zh.wikipedia.org/wiki/User:A2093064-bot/task/1/config/retention_time?action=raw";
$C["retention_time_default"] = 604800;
$C["retention_bytes"] = "https://zh.wikipedia.org/wiki/User:A2093064-bot/task/1/config/retention_bytes?action=raw";
$C["retention_bytes_default"] = 1000000;

$C["fail_retry"] = 5;

$C["summary_prefix"] = "[[User:A2093064-bot/task/1|機器人1]]";
$C["summary_config_page"] = "[[User:A2093064-bot/task/1/config|門檻]]";

$C["User-Agent"] = "User:A2093064-bot spam-blacklist-archive";

$C["cookiefile"] = __DIR__."/../tmp/spam-blacklist-archive-cookie.txt";
