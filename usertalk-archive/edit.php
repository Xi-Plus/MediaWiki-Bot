<?php
require(__DIR__."/../config/config.php");
if (!in_array(PHP_SAPI, $C["allowsapi"])) {
	exit("No permission");
}

set_time_limit(600);
date_default_timezone_set('UTC');
$starttime = microtime(true);
@include(__DIR__."/config.php");
require(__DIR__."/../function/curl.php");
require(__DIR__."/../function/login.php");
require(__DIR__."/../function/edittoken.php");

function converttime($chitime){
	if (preg_match("/(\d{4})年(\d{1,2})月(\d{1,2})日 \(.{3}\) (\d{2})\:(\d{2}) \(UTC\)/", $chitime, $m)) {
		return strtotime($m[1]."/".$m[2]."/".$m[3]." ".$m[4].":".$m[5]);
	} else {
		exit("converttime fail\n");
	}
}
function TimediffFormat($time) {
	if ($time<60) return $time."秒";
	if ($time<60*50) return round($time/60)."分";
	if ($time<60*60*23.5) return round($time/(60*60))."小時";
	return round($time/(60*60*24))."天";
}

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login();
$edittoken = edittoken();

$retention_time = file_get_contents($C["retention_time"]);
if ($retention_time === false) {
	$retention_time = $C["retention_time_default"];
	echo "Warning: fetch retention_time fail, use default value\n";
}
echo "archive before ".$retention_time." ago (".date("Y-m-d H:i:s", time()-$retention_time).")\n";

$to_page_number = file_get_contents($C["to_page_number"]);
if ($to_page_number === false) {
	$to_page_number = $C["to_page_number_default"];
	echo "Warning: fetch to_page_number fail, use default value\n";
}
echo "archive to ".$to_page_number."\n";

for ($i=$C["fail_retry"]; $i > 0; $i--) {
	$starttimestamp = time();
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $C["from_page"]
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	$text = $pages["revisions"][0]["*"];
	$basetimestamp = $pages["revisions"][0]["timestamp"];
	echo "get main page\n";

	$hash = md5(uniqid(rand(), true));
	$text = preg_replace("/^( *==.+?== *)$/m", $hash."$1", $text);
	$text = explode($hash, $text);
	echo "find ".count($text)." sections\n";

	$oldpagetext = $text[0];
	$newpagetext = "";
	$archive_count = 0;
	unset($text[0]);
	echo "start split\n";
	foreach ($text as $temp) {
		if (preg_match("/(==.+?==)/", $temp, $m)) {
			echo $m[1]."\n";
		} else {
			echo "title get fail\n";
		}
		preg_match_all("/\d{4}年\d{1,2}月\d{1,2}日 \(.{3}\) \d{2}\:\d{2} \(UTC\)/", $temp, $m);
		$firsttime = time();
		$lasttime = 0;
		foreach ($m[0] as $timestr) {
			$time = converttime($timestr);
			if ($time > time()) {
				echo "ignore time: ".date("Y/m/d H:i", $time)."\n";
				continue;
			}
			if ($time < $firsttime) $firsttime = $time;
			if ($time > $lasttime) $lasttime = $time;
		}
		echo "time=".date("Y/m/d H:i:s", $firsttime)."-".date("Y/m/d H:i:s", $lasttime)."\n";
		if (time()-$lasttime > $retention_time) {
			$newpagetext .= $temp;
			$archive_count++;
			echo "archive\t";
		} else {
			$oldpagetext.=$temp;
			echo "not archive\t";
		}
		echo "\n";
	}

	if ($newpagetext === "") {
		exit("no change\n");
	}

	echo "start edit\n";

	echo "edit main page\n";
	$summary = $C["summary_prefix"]."：存檔".$archive_count."章節 (".$C["summary_config_page"]."：".TimediffFormat($retention_time).")";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $C["from_page"],
		"summary" => $summary,
		"text" => $oldpagetext,
		"token" => $edittoken,
		"minor" => "",
		"starttimestamp" => $starttimestamp,
		"basetimestamp" => $basetimestamp
	);
	echo "edit ".$C["from_page"]." summary=".$summary."\n";
	if (!$C["test"]) $res = cURL($C["wikiapi"], $post);
	else $res = false;
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		if ($i === 1) {
			exit("quit\n");
		} else {
			echo "retry\n";
		}
	} else {
		break;
	}
}

$page = $C["to_page_prefix"].$to_page_number;
$starttimestamp2 = time();
$res = cURL($C["wikiapi"]."?".http_build_query(array(
	"action" => "query",
	"prop" => "revisions",
	"format" => "json",
	"rvprop" => "content|timestamp",
	"titles" => $page
)));
$res = json_decode($res, true);
$pages = current($res["query"]["pages"]);
$oldtext = "{{Talkarchive}}\n";
$basetimestamp2 = null;
if (!isset($pages["missing"])) {
	$oldtext = $pages["revisions"][0]["*"];
	$basetimestamp2 = $pages["revisions"][0]["timestamp"];
	echo $page." exist\n";
} else {
	echo $page." not exist\n";
}

$summary = $C["summary_prefix"]."：存檔自[[".$C["from_page"]."]]共".$archive_count."個章節";
$post = array(
	"action" => "edit",
	"format" => "json",
	"title" => $page,
	"summary" => $summary,
	"text" => $oldtext."\n".$newpagetext,
	"token" => $edittoken,
	"starttimestamp" => $starttimestamp2
);
if ($basetimestamp2 !== null) {
	$post["basetimestamp"] = $basetimestamp2;
}
echo "edit ".$page." summary=".$summary."\n";
for ($i=$C["fail_retry"]; $i > 0; $i--) { 
	if (!$C["test"]) $res = cURL($C["wikiapi"], $post);
	else $res = false;
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		if ($i === 1) {
			exit("quit\n");
		} else {
			echo "retry\n";
		}
	} else {
		break;
	}
}
echo "saved\n";

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
