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

$res = cURL($C["wikiapi"]."?".http_build_query(array(
	"action" => "query",
	"format" => "json",
	"list" => "categorymembers",
	"cmtitle" => $C["category"],
	"cmlimit" => "max"
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
$pagelist = $res["query"]["categorymembers"];
foreach ($pagelist as $page) {
	for ($i=$C["fail_retry"]; $i > 0; $i--) {
		$starttimestamp = time();
		$res = cURL($C["wikiapi"]."?".http_build_query(array(
			"action" => "query",
			"prop" => "revisions",
			"format" => "json",
			"rvprop" => "content|timestamp",
			"pageids" => $page["pageid"]
		)));
		if ($res === false) {
			exit("fetch page fail\n");
		}
		$res = json_decode($res, true);
		$pages = current($res["query"]["pages"]);
		$text = $pages["revisions"][0]["*"];
		$basetimestamp = $pages["revisions"][0]["timestamp"];

		$text = preg_replace("/{{Draft Copyvio}} *\n*/i", "", $text);
		$text = preg_replace("/<!--請勿刪除此行，並由下一行開始編輯--> *\n*/i", "", $text);

		$summary = $C["summary_prefix"]."，移除{{Draft Copyvio}}";
		$post = array(
			"action" => "edit",
			"format" => "json",
			"pageid" => $page["pageid"],
			"summary" => $summary,
			"text" => $text,
			"token" => $edittoken,
			"minor" => "",
			"starttimestamp" => $starttimestamp,
			"basetimestamp" => $basetimestamp
		);
		echo "edit ".$page["title"]." summary=".$summary."\n";
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
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
