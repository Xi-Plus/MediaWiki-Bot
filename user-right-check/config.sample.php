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

$C['TIME_MIN'] = '1970-01-01 08:00:01';

$C["AWBright"] = "AWB";
$C["AWBname"] = "自動維基瀏覽器使用權";

$C["day"] = array("日", "一", "二", "三", "四", "五", "六");

$C["other_report_page"] = "Wikipedia:申请解除权限";
$C["other_report_text"] = "==已封禁或除权用户覆审==";
$C["other_report_summary_prefix"] = "/* 逾六个月没有任何编辑活动 */ [[User:A2093064-bot/task/12|機器人12]]：新提案";
$C["other_report_timelimit"] = "-184 days";
$C["other_report_limit"] = 10;

$C["other_update_timelimit"] = "-5 months";

$C["other_exporttable_timelimit1"] = "-5 months";
$C["other_exporttable_timelimit2"] = "-184 days";
$C["other_exporttable_timelimit3"] = "-177 days";
$C["other_exporttable_page"] = "User:A2093064-bot/task/13/output/revoke";
$C["other_exporttable_summary_prefix"] = "[[User:A2093064-bot/task/13|機器人13]]：檢查持權用戶活躍狀況：";
$C["other_exporttable_text1"] = "<!--revoke table start-->";
$C["other_exporttable_text2"] = "<!--revoke table end-->";
$C["other_exporttable_text3"] = "<!--sign start-->";
$C["other_exporttable_text4"] = "<!--sign end-->";

$C["other_export_timelimit"] = "-184 days";

$C["other_notice_timelimit1"] = "-177 days";
$C["other_notice_timelimit2"] = "-3 months";
$C["other_notice_text1"] = "Template:Inactive IPBE";
$C["other_notice_text2"] = "Template:Inactive right";
$C["other_notice_limit"] = 10;
$C["other_notice_summary_prefix"] = "[[User:A2093064-bot/task/12|機器人12]]：通知不活躍用戶除權通知";

$C["other_result_timelimit"] = "-184 days";

$C["fail_retry"] = 5;

$C["User-Agent"] = "User:A2093064-bot user-right-check";

$C["DBTBprefix"] = "user_right_check_";

$C["cookiefile"] = __DIR__."/../tmp/user-right-check-cookie.txt";

$C["fail_retry"] = 5;

$G["db"] = new PDO ('mysql:host='.$C["DBhost"].';dbname='.$C["DBname"].';charset=utf8mb4', $C["DBuser"], $C["DBpass"]);
