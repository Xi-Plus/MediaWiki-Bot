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

$blocked_retention_time = file_get_contents($C["blocked_retention_time"]);
if ($blocked_retention_time === false) {
	$blocked_retention_time = $C["blocked_retention_time_default"];
	echo "Warning: fetch blocked_retention_time fail, use default value\n";
}
echo "blocked archive before ".$blocked_retention_time." ago (".date("Y-m-d H:i:s", time()-$blocked_retention_time).")\n";
$other_retention_time = file_get_contents($C["other_retention_time"]);
if ($other_retention_time === false) {
	$other_retention_time = $C["other_retention_time_default"];
	echo "Warning: fetch other_retention_time fail, use default value\n";
}
echo "other archive before ".$other_retention_time." ago (".date("Y-m-d H:i:s", time()-$other_retention_time).")\n";
$year = date("Y");

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

	$start = strpos($text, $C["text1"]);
	$oldpagetext = substr($text, 0, $start+strlen($C["text1"]))."\n";
	$text = substr($text, $start+strlen($C["text1"]));
	$newpagetext = "";

	$hash = md5(uniqid(rand(), true));
	$text = preg_replace("/^(\*[^*:])/mi", $hash."$1", $text);
	$text = explode($hash, $text);
	unset($text[0]);
	echo "find ".count($text)." reports\n";

	$archive_count = 0;
	foreach ($text as $temp) {
		$blocked = false;
		if (preg_match("/{{user-uaa\|(?:1=)?(.+?)}}/", $temp, $m)) {
			$user = $m[1];
			echo "User:".$user."\t";
			$res = cURL($C["wikiapi"]."?".http_build_query(array(
				"action" => "query",
				"format" => "json",
				"list" => "users",
				"usprop" => "blockinfo",
				"ususers" => $user
			)));
			if ($res === false) {
				exit("fetch page fail\n");
			}
			$res = json_decode($res, true);
			$blocked = isset($res["query"]["users"][0]["blockexpiry"]) && $res["query"]["users"][0]["blockexpiry"] === "infinity";
		} else {
			echo "Unknown user\t";
		}
		echo ($blocked?"blocked":"not blocked")."\t";

		if (preg_match_all("/\d{4}年\d{1,2}月\d{1,2}日 \(.{3}\) \d{2}\:\d{2} \(UTC\)/", $temp, $m)) {
			$lasttime = 0;
			foreach ($m[0] as $timestr) {
				$time = converttime($timestr);
				if ($time > $lasttime) $lasttime = $time;
			}
		} else {
			$lasttime = time();
		}
		echo date("Y/m/d H:i", $lasttime)."\t";

		if (time()-$lasttime > ($blocked ? $blocked_retention_time : $other_retention_time)) {
			echo "archive\n";
			$newpagetext .= $temp;
			$archive_count++;
		} else {
			echo "not archive\n";
			$oldpagetext .= $temp;
		}
	}

	if ($archive_count === 0) {
		exit("no change\n");
	}

	echo "start edit\n";

	echo "edit main page\n";
	$summary = $C["summary_prefix"]."：存檔".$archive_count."提案 (".$C["summary_config_page"]."：已封禁".TimediffFormat($blocked_retention_time)."、未處理".TimediffFormat($other_retention_time).")";
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
	else {
		$res = false;
		file_put_contents("out1.txt", $oldpagetext);
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		if ($i === 1) {
			exit("quit\n");
		} else {
			echo "retry\n";
			continue;
		}
	} else {
		echo "saved\n";
	}

	echo "edit archive page\n";
	$page = $C["to_page_prefix"].$year."年";
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

	$oldtext = "{{存档页}}
{{Wikipedia:需要管理員注意的用戶名/Archive}}
=== {$year}年 ===\n";

	$basetimestamp2 = null;
	if (!isset($pages["missing"])) {
		$oldtext = $pages["revisions"][0]["*"];
		$basetimestamp2 = $pages["revisions"][0]["timestamp"];
		echo $page." exist\n";
	} else {
		echo $page." not exist\n";
	}

	$oldtext .= "\n".$newpagetext;

	$text = preg_replace("/\n{3,}/", "\n\n", $oldtext);

	$summary = $C["summary_prefix"]."：存檔自[[".$C["from_page"]."]]共".$archive_count."個提案";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $page,
		"summary" => $summary,
		"text" => $text,
		"token" => $edittoken,
		"minor" => "",
		"starttimestamp" => $starttimestamp2
	);
	if ($basetimestamp2 !== null) {
		$post["basetimestamp"] = $basetimestamp2;
	}
	echo "edit ".$page." summary=".$summary."\n";
	if (!$C["test"]) $res = cURL($C["wikiapi"], $post);
	else {
		$res = false;
		file_put_contents("out2.txt", $text);
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		if ($i === 1) {
			exit("quit\n");
		} else {
			echo "retry\n";
			continue;
		}
	} else {
		echo "saved\n";
		break;
	}
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
