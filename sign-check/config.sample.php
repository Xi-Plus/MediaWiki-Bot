<?php

$C["wikiapi"] = "https://zh.wikipedia.org/w/api.php";
$C["user"] = "";
$C["pass"] = "";

$C['TIME_MIN'] = '1970-01-01 08:00:01';

$C["timelimit"] = "-1 weeks";

$C["text1"] = "<!--table start-->";
$C["text2"] = "<!--table end-->";
$C["text3"] = "<!--sign start-->";
$C["text4"] = "<!--sign end-->";

$C["quarry"] = "https://quarry.wmflabs.org/query/21467";

$C["page"] = "User:A2093064-bot/task/14/output/status";

$C["fail_retry"] = 5;

$C["summary_prefix"] = "[[User:A2093064-bot/task/14|機器人14]]：檢查簽名：";

$C["User-Agent"] = "User:A2093064-bot sign-check";

$C["DBTBprefix"] = "sign_check_";

$C["cookiefile"] = __DIR__ . "/../tmp/sign-check-cookie.txt";

$G["db"] = new PDO('mysql:host=' . $C["DBhost"] . ';dbname=' . $C["DBname"] . ';charset=utf8mb4', $C["DBuser"], $C["DBpass"]);
