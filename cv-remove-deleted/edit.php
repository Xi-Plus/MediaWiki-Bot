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

$start = strpos($text, $C["text1"]);
$oldpagetext = substr($text, 0, $start+strlen($C["text1"]));
$text = substr($text, $start+strlen($C["text1"]));

$hash = md5(uniqid(rand(), true));
$text = preg_replace("/^(===.+?===\s*)$/m", $hash."$1", $text);
$text = explode($hash, $text);
echo "find ".(count($text)-1)." sections\n";

$oldpagetext .= $text[0];
unset($text[0]);

$totalcount = 0;
foreach ($text as $temp) {
	if (preg_match("/===(\d+)月(\d+)日===\s*/", $temp, $m)) {
		$year = $m[1];
		$month = $m[2];
		echo $year."/".$month."\t";
	} else {
		echo "title get fail\t";
	}

	preg_match_all("/{{CopyvioEntry\|1=([^|]+)\|/", $temp, $m);
	$titles = implode("|", $m[1]);
	echo "find ".count($m[1])." titles\t";

	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "",
		"titles" => $titles
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$missing = [];
	foreach ($res["query"]["pages"] as $page) {
		if (isset($page["missing"])) {
			$missing []= $page["title"];
		}
	}

	$hash = md5(uniqid(rand(), true));
	$temp = preg_replace("/^(.*{{CopyvioEntry\|.+)$/m", $hash."$1", $temp);
	$temp = explode($hash, $temp);
	$origincount = (count($temp)-1);
	echo "find ".$origincount." sections\n";

	$oldpagetexttemp = $temp[0];
	unset($temp[0]);

	$count = 0;
	foreach ($temp as $temp2) {
		if (preg_match("/{{CopyvioEntry\|1=([^|]+)\|/", $temp2, $m)) {
			if (in_array($m[1], $missing)) {
				echo "\tremove ".$m[1];

				$res = cURL($C["wikiapi"]."?".http_build_query(array(
					"action" => "query",
					"format" => "json",
					"list" => "logevents",
					"leprop" => "comment",
					"letype" => "delete",
					"letitle" => $m[1],
					"lelimit" => "1"
				)));
				if ($res === false) {
					exit("fetch page fail\n");
				}
				$res = json_decode($res, true);
				echo "\t".$res["query"]["logevents"][0]["comment"]."\n";

				$count++;
				$totalcount++;
			} else {
				$oldpagetexttemp .= $temp2;
			}
		} else {
			$oldpagetexttemp .= $temp2;
		}
	}

	if ($origincount != $count) {
		$oldpagetext .= $oldpagetexttemp;
	} else {
		echo "empty section\n";
	}
}
echo "total remove ".$totalcount."\n";
$text = $oldpagetext;

$summary = $C["summary_prefix"];
$post = array(
	"action" => "edit",
	"format" => "json",
	"title" => $C["page"],
	"summary" => $summary,
	"text" => $text,
	"token" => $edittoken,
	"starttimestamp" => $starttimestamp,
	"basetimestamp" => $basetimestamp
);
echo "edit ".$C["page"]." summary=".$summary."\n";
if (!$C["test"]) {
	$res = cURL($C["wikiapi"], $post);
} else {
	$res = false;
	file_put_contents(__DIR__."/out.txt", $text);
}
$res = json_decode($res, true);
if (isset($res["error"])) {
	echo "edit fail\n";
	var_dump($res["error"]);
}
