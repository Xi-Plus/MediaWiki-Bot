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

$C["summary_prefix"] = "[[User:A2093064-bot/task/12|機器人12]]：新提案，提報六個月無活動用戶";

$C["text"] = "==已封禁或除权用户覆审==";

$C["other_timelimit"] = "-6 months";
$C["report_limit"] = 10;
$C["fail_retry"] = 5;

$C["User-Agent"] = "User:A2093064-bot user-right-check";

$C["DBTBprefix"] = "user_right_check_";

$C["cookiefile"] = __DIR__."/../tmp/user-right-check-cookie.txt";

$G["db"] = new PDO ('mysql:host='.$C["DBhost"].';dbname='.$C["DBname"].';charset=utf8mb4', $C["DBuser"], $C["DBpass"]);
