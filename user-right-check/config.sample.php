<?php

$C["wikiapi"] = "https://zh.wikipedia.org/w/api.php";
$C["page"] = "Wikipedia:申请解除权限";
$C["AWBpage"] = "https://zh.wikipedia.org/wiki/Wikipedia:AutoWikiBrowser/CheckPage?action=raw";
$C["user"] = "";
$C["pass"] = "";

$C["right-whitelist"] = array(
	"*",
	"user",
	"autoconfirmed",
	"confirmed",
	"bot"
);

$C["AWBright"] = "AWB";
$C["AWBname"] = "自動維基瀏覽器使用權";

$C["day"] = array("日", "一", "二", "三", "四", "五", "六");

$C["other_report_page"] = "Wikipedia:申请解除权限";
$C["other_report_text"] = "==已封禁或除权用户覆审==";
$C["other_report_summary_prefix"] = "[[User:A2093064-bot/task/12|機器人12]]：新提案，提報六個月無活動用戶";
$C["other_report_timelimit"] = "-6 months";
$C["other_report_limit"] = 10;

$C["other_exporttable_page"] = "User:A2093064-bot/task/13/output/revoke";
$C["other_exporttable_summary_prefix"] = "[[User:A2093064-bot/task/13|機器人13]]：檢查持權用戶活躍狀況：";

$C["fail_retry"] = 5;

$C["User-Agent"] = "User:A2093064-bot user-right-check";

$C["DBTBprefix"] = "user_right_check_";

$C["cookiefile"] = __DIR__."/../tmp/user-right-check-cookie.txt";

$C["fail_retry"] = 5;

$G["db"] = new PDO ('mysql:host='.$C["DBhost"].';dbname='.$C["DBname"].';charset=utf8mb4', $C["DBuser"], $C["DBpass"]);
