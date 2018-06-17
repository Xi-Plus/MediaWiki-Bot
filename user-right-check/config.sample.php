<?php

$C["wikiapi"] = "https://zh.wikipedia.org/w/api.php";
$C["config_page_notice"] = "https://zh.wikipedia.org/w/index.php?title=User:A2093064-bot/task/12/config.json&action=raw";
$C["config_page_exporttable"] = "https://zh.wikipedia.org/w/index.php?title=User:A2093064-bot/task/13/config.json&action=raw";
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

$C['TIME_MIN'] = '1970-01-01 08:00:01';

$C["AWBright"] = "AWB";
$C["AWBname"] = "自動維基瀏覽器使用權";

$C["day"] = array("日", "一", "二", "三", "四", "五", "六");

$C["other_report_page"] = "Wikipedia:申请解除权限";
$C["other_report_text"] = "==已封禁或除权用户覆审==";
$C["other_report_summary_prefix"] = "/* 逾六个月没有任何编辑活动 */ [[User:A2093064-bot/task/12|機器人12]]：新提案";
$C["other_report_timelimit"] = "-184 days";
$C["other_report_notice_timelimit"] = "-31 days";
$C["other_report_limit"] = 10;

$C["other_update_timelimit"] = "-5 months +7 days";

$C["other_export_timelimit"] = "-184 days";

$C["other_result_timelimit"] = "-184 days";

$C["bot_result_timelimit"] = "-1 year";

$C["User-Agent"] = "User:A2093064-bot user-right-check";

$C["DBTBprefix"] = "user_right_check_";

$C["cookiefile"] = __DIR__."/../tmp/user-right-check-cookie.txt";

$C["fail_retry"] = 5;

$G["db"] = new PDO ('mysql:host='.$C["DBhost"].';dbname='.$C["DBname"].';charset=utf8mb4', $C["DBuser"], $C["DBpass"]);
