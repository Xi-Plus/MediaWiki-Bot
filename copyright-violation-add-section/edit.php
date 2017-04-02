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

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login();
$edittoken = edittoken();

$month = date("n");
$date = date("j");
$tag_timestamp = mktime(0, 0, 0, $month, $date)+86400*7;
echo "tag ".$month."月".$date."日 (timestamp > ".$tag_timestamp.")\n";

for ($i=$C["fail_retry"]; $i > 0; $i--) {
	$starttimestamp = time();
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $C["page"]
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	$text = $pages["revisions"][0]["*"];
	$basetimestamp = $pages["revisions"][0]["timestamp"];
	echo "get main page\n";

	if (preg_match("/=== *{$month}月{$date}日 *===/", $text)) {
		exit("find today section. exit.\n");
	}

	$hash = md5(uniqid(rand(), true));
	$text = preg_replace("/^({{CopyvioEntry\|)/m", $hash."$1", $text);
	$text = explode($hash, $text);
	echo "find ".count($text)." sections\n";

	$pagetext = $text[0];
	unset($text[0]);
	echo "start split\n";
	$nochange = true;
	foreach ($text as $temp) {
		if (preg_match("/{{CopyvioEntry\|1=.+?\|time=(\d+?)\|/", $temp, $m)) {
			echo $m[0]."\t";
		} else {
			echo "get timestamp fail\t";
		}
		if ($nochange && $m[1] >= $tag_timestamp) {
			$pagetext .= "===".$month."月".$date."日===\n";
			echo "tag before\t";
			$nochange = false;
		}
		$pagetext.=$temp;
		echo "\n";
	}

	if ($nochange) {
		exit("no change\n");
	}

	echo "start edit\n";

	echo "edit main page\n";
	$summary = $C["summary_prefix"]."：標記".$month."月".$date."日";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $C["page"],
		"summary" => $summary,
		"text" => $pagetext,
		"token" => $edittoken,
		"minor" => "",
		"starttimestamp" => $starttimestamp,
		"basetimestamp" => $basetimestamp
	);
	echo "edit ".$C["page"]." summary=".$summary."\n";
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

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
