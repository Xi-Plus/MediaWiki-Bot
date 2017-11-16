<?php
require(__DIR__."/../config/config.php");
if (!in_array(PHP_SAPI, $C["allowsapi"])) {
	exit("No permission");
}

set_time_limit(600);
date_default_timezone_set('UTC');
$starttime = microtime(true);
@include(__DIR__."/config.php");
@include(__DIR__."/function.php");
require(__DIR__."/../function/curl.php");
require(__DIR__."/../function/login.php");
require(__DIR__."/../function/edittoken.php");

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login();
$C["edittoken"] = edittoken();

$lasttimefile = __DIR__."/lasttime.txt";
$lasttime = @file_get_contents($lasttimefile);
file_put_contents($lasttimefile, date("Y-m-d\TH:i:s\Z"));
if ($lasttime === false) {
	$lasttime = date("Y-m-d\TH:i:s\Z", strtotime("-1 weeks"));
}
file_put_contents(__DIR__."/lasttime-old.txt", $lasttime);
echo "lasttime: ".$lasttime."\n";
$res = cURL($C["wikiapi"]."?".http_build_query(array(
	"action" => "query",
	"format" => "json",
	"prop" => "revisions",
	"titles" => $C["from_page"],
	"rvprop" => "ids|user|timestamp",
	"rvlimit" => "max",
	"rvend" => $lasttime
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
$page = current($res["query"]["pages"]);
if (!isset($page["revisions"])) {
	exit("no new\n");
}
$revisions = $page["revisions"];
foreach ($revisions as $revision) {
	echo $revision["revid"]." ".$revision["parentid"]." ".$revision["user"]." ".$revision["timestamp"]."\n";
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "compare",
		"format" => "json",
		"fromrev" => $revision["parentid"],
		"torev" => $revision["revid"]
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$diff = $res["compare"]["*"];
	$result = parsediff($diff);
	if ($result["result"]) {
		echo $result["section"]." ".$result["status"]." ";
		$text = getrevcontent($revision["revid"]);
		$firsttime = getfirsttime($text, $result["section"]);
		$date = date("Y/m/d", $firsttime);
		echo $date."\n";
		tagtalkpage($result["page"], $date, $revision["revid"], $result["status"]);
	}
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
