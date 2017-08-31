<?php
require(__DIR__."/../config/config.php");
date_default_timezone_set('UTC');
@include(__DIR__."/config.php");
require(__DIR__."/../function/curl.php");
require(__DIR__."/../function/login.php");
require(__DIR__."/../function/edittoken.php");
require(__DIR__."/../function/log.php");

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login();
$edittoken = edittoken();

$timelimit = date("Y-m-d H:i:s", strtotime($C["other_exporttable_timelimit1"]));
echo "顯示最後動作 < ".$timelimit." (".("-5 months").")\n";
$timelimit2 = date("Y-m-d H:i:s", strtotime($C["other_exporttable_timelimit2"]));
$timelimit3 = date("Y-m-d H:i:s", strtotime($C["other_exporttable_timelimit3"]));

$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist` WHERE `lasttime` < :lasttime ORDER BY `lasttime` ASC");
$sth->bindValue(":lasttime", $timelimit);
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);

foreach ($row as $key => $user) {
	$row[$key]["rights"] = explode("|", $row[$key]["rights"]);
	if (in_array("bot", $row[$key]["rights"])) {
		$row[$key]["rights"] = array_diff($row[$key]["rights"], ["AWB"]);
	}
	$row[$key]["rights"] = array_diff($row[$key]["rights"], $C["right-whitelist"]);
	$row[$key]["rights"] = array_values($row[$key]["rights"]);
	if (count($row[$key]["rights"]) == 0) {
		unset($row[$key]);
	}
}
$row = array_values($row);

echo "共有".count($row)."筆\n\n";
$out = "";
$count = 1;
$out .= '{| class="wikitable"
|-
! 用戶 !! width="80"|權限 !! 最後編輯 !! 最後日誌動作 !! 最後授權';
foreach ($row as $user) {
	$out .= '
|-';
if ($user["lasttime"] < $timelimit2) {
	$out .= ' style="background: #fcc;"';
} else if ($user["lasttime"] < $timelimit3) {
	$out .= ' style="background: #ffc;"';
}
	$out .= '
| [[User:'.$user["name"].'|'.$user["name"].']] [[User talk:'.$user["name"].'|T]] || [[Special:用户权限/'.$user["name"].'|';
	foreach ($user["rights"] as $key => $value) {
		if ($key) {
			$out .= '、';
		}
		if ($value == $C["AWBright"]) {
			$out .= $C["AWBname"];
		} else {
			$out .= '{{int:group-'.$value.'}}';
		}
	}
	$out .= ']] || [[Special:用户贡献/'.$user["name"].'|';
	if ($user["lastedit"] == $C['TIME_MIN']) {
		$out .= "從未編輯過";
	} else {
		$time = strtotime($user["lastedit"]);
		$out .= date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
	}
	$out .= ']] || [[Special:日志/'.$user["name"].'|';
	if ($user["lastlog"] == $C['TIME_MIN']) {
		$out .= "從未有日誌動作";
	} else {
		$time = strtotime($user["lastlog"]);
		$out .= date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
	}
	$out .= ']] || [https://zh.wikipedia.org/wiki/Special:日志/rights?page=User:'.str_replace(" ", "_", $user["name"]).' ';
	$time = strtotime($user["lastusergetrights"]);
	$out .= date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
	$out .= ']';
}
$out .= '
|}';

for ($i=$C["fail_retry"]; $i > 0; $i--) {
	$starttimestamp = time();
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $C["other_exporttable_page"]
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	$text = $pages["revisions"][0]["*"];
	$basetimestamp = $pages["revisions"][0]["timestamp"];

	$start = strpos($text, $C["other_exporttable_text1"]);
	$end = strpos($text, $C["other_exporttable_text2"]);
	$text = substr($text, 0, $start).$C["other_exporttable_text1"].$out.substr($text, $end);

	$start = strpos($text, $C["other_exporttable_text3"]);
	$end = strpos($text, $C["other_exporttable_text4"]);
	$text = substr($text, 0, $start).$C["other_exporttable_text3"]."~~~~".substr($text, $end);

	$summary = $C["other_exporttable_summary_prefix"]."更新";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $C["other_exporttable_page"],
		"summary" => $summary,
		"text" => $text,
		"minor" => "",
		"token" => $edittoken
	);
	echo "edit ".$C["other_exporttable_page"]." summary=".$summary."\n";
	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
		file_put_contents(__DIR__."/out.txt", $out);
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		continue;
	}
	break;
}
