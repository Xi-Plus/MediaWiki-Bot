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
function convertdate($chitime){
	if (preg_match("/(\d{4})年(\d{1,2})月(\d{1,2})日 \(.{3}\) \d{2}\:\d{2} \(UTC\)/", $chitime, $m)) {
		return strtotime($m[1]."/".$m[2]."/".$m[3]);
	} else {
		exit("convertdate fail\n");
	}
}
function TimediffFormat($time) {
	if ($time<60) return $time."秒";
	if ($time<60*50) return round($time/60)."分";
	if ($time<60*60*23.5) return round($time/(60*60))."小時";
	return round($time/(60*60*24))."天";
}

echo "現在時間: ".date("Y-m-d H:i:s")."\n";

login();
$edittoken = edittoken();
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
	echo "get now page\n";

	$hash = md5(uniqid(rand(), true));
	$text = preg_replace("/^( *==.+?== *)$/m", $hash."$1", $text);
	$text = explode($hash, $text);
	echo "find ".count($text)." sections\n";

	$oldpagetext = $text[0];
	$newpagetext = array();
	$archive_count = array("all" => 0);
	unset($text[0]);
	echo "start split\n";
	echo "存檔 ".date("Y-m-d H:i:s", time()-$C["archive_ago"])." 以前\n";
	foreach ($text as $temp) {
		if (preg_match("/(==.+?==)/", $temp, $m)) {
			echo "title is ".$m[1]."\n";
		} else {
			echo "title get fail\n";
		}
		preg_match_all("/\d{4}年\d{1,2}月\d{1,2}日 \(.{3}\) \d{2}\:\d{2} \(UTC\)/", $temp, $m);
		$firsttime = time();
		$lasttime = 0;
		foreach ($m[0] as $timestr) {
			$time = converttime($timestr);
			if ($time < $firsttime) $firsttime = $time;
			if ($time > $lasttime) $lasttime = $time;
		}
		echo "firsttime = ".date("Y/m/d H:i:s", $firsttime)."\n";
		echo "lasttime = ".date("Y/m/d H:i:s", $lasttime)."\n";
		if (time()-$lasttime > $C["archive_ago"]) {
			$date = date("Y年n月j日", $firsttime);
			if (!isset($newpagetext[$date])) {
				$newpagetext[$date] = "";
				$archive_count[$date] = 0;
			}
			$newpagetext[$date] .= $temp;
			$archive_count[$date]++;
			$archive_count["all"]++;
			echo "archive to ".$date."\n";
		} else {
			$oldpagetext.=$temp;
			echo "not archive\n";
		}
		echo "\n";
	}

	if ($archive_count["all"] === 0) {
		exit("no change\n");
	}

	echo "start edit\n";

	echo "edit current page\n";
	$summary = "[[Wikipedia:机器人/申请/A2093064-bot|機器人測試]]：存檔超過".TimediffFormat($C["archive_ago"])."無變更的章節，共".$archive_count["all"]."個章節存檔至".count($newpagetext)."個頁面";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $C["from_page"],
		"summary" => $summary,
		"text" => $oldpagetext,
		"token" => $edittoken,
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

echo "edit archive page\n";
foreach ($newpagetext as $date => $newtext) {
	$page = $C["to_page_prefix"].$date;
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
	$oldtext = "{{Talkarchive|MediaWiki talk:Spam-blacklist}}\n";
	$basetimestamp2 = null;
	if (!isset($pages["missing"])) {
		$oldtext = $pages["revisions"][0]["*"];
		$basetimestamp2 = $pages["revisions"][0]["timestamp"];
		echo $page." exist\n";
	} else {
		echo $page." not exist\n";
	}

	$summary = "[[Wikipedia:机器人/申请/A2093064-bot|機器人測試]]：存檔自[[".$C["from_page"]."]]共".$archive_count[$date]."個章節";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $page,
		"summary" => $summary,
		"text" => $oldtext."\n".$newtext,
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
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";

// $post=array(
// 	"appendtext"=>"\n*已存檔".count($newpagetext)."天，花了".$spendtime."秒。--~~~~",
// 	"token"=>$token
// );
// $res = cURL($C["wikiapi"]."?action=edit&format=json&title=".$C["log_page"]."&summary=存檔log",$post,false,$C["cookiefile"]);
// $res=json_decode($res->html);
// echo "edit log\n";
