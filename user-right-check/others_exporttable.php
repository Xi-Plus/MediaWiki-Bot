<?php
require(__DIR__."/../config/config.php");
date_default_timezone_set('UTC');
@include(__DIR__."/config.php");
require(__DIR__."/../function/curl.php");
require(__DIR__."/../function/login.php");
require(__DIR__."/../function/edittoken.php");
require(__DIR__."/../function/log.php");

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

$config_page = file_get_contents($C["config_page_exporttable"]);
if ($config_page === false) {
	exit("get config failed\n");
}
$cfg = json_decode($config_page, true);

if (!$cfg["enable"]) {
	exit("disabled\n");
}

var_dump($cfg);

login("bot");
$edittoken = edittoken();

$timelimit = date("Y-m-d H:i:s", strtotime($cfg["time_to_display"]));
echo "顯示最後動作 < ".$timelimit." (".$cfg["time_to_display"].")\n";
$timelimit2 = date("Y-m-d H:i:s", strtotime($cfg["time_to_revoke"]));
$timelimit3 = date("Y-m-d H:i:s", strtotime($cfg["time_to_notice"]));

$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist` WHERE `lasttime` < :lasttime ORDER BY `lasttime` ASC");
$sth->bindValue(":lasttime", $timelimit);
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);

foreach ($row as $key => $user) {
	$row[$key]["rights"] = explode("|", $row[$key]["rights"]);
	if (in_array("bot", $row[$key]["rights"])) {
		$row[$key]["rights"] = array_diff($row[$key]["rights"], ["AWB"]);
	}
	$row[$key]["rights"] = array_diff($row[$key]["rights"], $cfg["right_not_to_display"]);
	$row[$key]["rights"] = array_values($row[$key]["rights"]);
	if (count($row[$key]["rights"]) == 0) {
		unset($row[$key]);
	}
}
$row = array_values($row);

echo "共有".count($row)."筆\n\n";
$count = 1;
$tabletext = $cfg["output_page_table_header"];
foreach ($row as $cnt => $user) {
	if ($user["lasttime"] < $timelimit2) {
		$rowcolor = $cfg["output_page_color_for_revoke"];
	} else if ($user["lasttime"] < $timelimit3) {
		$rowcolor = $cfg["output_page_color_for_notice"];
	} else {
		$rowcolor = $cfg["output_page_color_for_display"];
	}
	$rightlist = "";
	foreach ($user["rights"] as $key => $value) {
		if ($key) {
			$rightlist .= '、';
		}
		if ($value == $C["AWBright"]) {
			$rightlist .= $cfg["right_awb_name"];
		} else {
			$rightlist .= '{{int:group-'.$value.'}}';
		}
	}
	if ($user["lastedit"] == $C['TIME_MIN']) {
		$lastedit = "從未編輯過";
	} else {
		$time = strtotime($user["lastedit"]);
		$lastedit = date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
	}
	if ($user["lastlog"] == $C['TIME_MIN']) {
		$lastlog = "從未有日誌動作";
	} else {
		$time = strtotime($user["lastlog"]);
		$lastlog = date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
	}
	$time = strtotime($user["lastusergetrights"]);
	$lastright = date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
	$tabletext .= sprintf($cfg["output_page_table_row"],
		$rowcolor,
		($cnt+1),
		str_replace(" ", "_", $user["name"]),
		$rightlist,
		$lastedit,
		$lastlog,
		$lastright
	);
}
$tabletext .= $cfg["output_page_table_footer"];

$text = sprintf($cfg["output_page_content"], $tabletext);

$summary = $cfg["output_page_summary"];
$post = array(
	"action" => "edit",
	"format" => "json",
	"title" => $cfg["output_page_name"],
	"summary" => $summary,
	"text" => $text,
	"minor" => "",
	"token" => $edittoken
);
echo "edit ".$cfg["output_page_name"]." summary=".$summary."\n";
if (!$C["test"]) {
	$res = cURL($C["wikiapi"], $post);
} else {
	$res = false;
	file_put_contents(__DIR__."/out.txt", $text);
}
$res = json_decode($res, true);
if (isset($res["error"])) {
	exit("edit fail\n");
}
