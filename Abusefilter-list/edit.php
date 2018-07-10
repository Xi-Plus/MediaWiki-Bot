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

$options = getopt("t", ["test"]);
if ($options === false) {
	exit("parse parameter failed\n");
}
if (isset($options["t"]) || isset($options["test"])) {
	$C["test"] = true;
}

if ($C["test"]) {
	echo "test mode on.\n";
}

login();
$edittoken = edittoken();

$res = cURL($C["wikiapi"]."?".http_build_query(array(
	"action" => "query",
	"format" => "json",
	"list" => "abusefilters",
	"abflimit" => "max",
	"abfprop" => "id|description|actions|status|private|hits"
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);

$out = '{| class="wikitable sortable" style="background-color: #fff;"
|- 
! style="background-color: #ddf;"| {{int:abusefilter-list-id}}
! style="background-color: #ddf;"| {{int:abusefilter-list-public}}
! style="background-color: #ddf;"| {{int:abusefilter-list-consequences}}
! style="background-color: #ddf;"| {{int:abusefilter-list-status}}
! style="background-color: #ddf;"| {{int:abusefilter-list-visibility}}
! style="background-color: #ddf;"| {{int:abusefilter-list-hitcount}}
';
$outcsv = [];
foreach ($res["query"]["abusefilters"] as $AF) {
	$action = $AF["actions"];
	$action = str_replace("warn", "{{int:abusefilter-action-warn}}", $action);
	$action = str_replace("tag", "{{int:abusefilter-action-tag}}", $action);
	$action = str_replace("disallow", "{{int:abusefilter-action-disallow}}", $action);
	$action = str_replace("throttle", "{{int:abusefilter-action-throttle}}", $action);
	$action = str_replace("blockautopromote", "{{int:abusefilter-action-blockautopromote}}", $action);
	$action = str_replace(",", "、", $action);

	if ($AF["hits"] > 1000) {
		$AF["hits"] = (floor($AF["hits"]/1000)*1000);
		$AFhitstext = $AF["hits"]." 次以上命中";
	} else if ($AF["hits"] > 100) {
		$AF["hits"] = (floor($AF["hits"]/100)*100);
		$AFhitstext = $AF["hits"]." 次以上命中";
	} else {
		$AFhitstext = $AF["hits"]." 次命中";
	}

	$out .= '|- style="color: '.(isset($AF["enabled"])?"#000":(isset($AF["deleted"])?"#aaa":"#666")).';"
| [[Special:AbuseFilter/'.$AF["id"].'|'.$AF["id"].']]
| [[Special:AbuseFilter/'.$AF["id"].'|'.$AF["description"].']]
|'.$action.'
|'.(isset($AF["enabled"])?"{{int:abusefilter-enabled}}":(isset($AF["deleted"])?"{{int:abusefilter-deleted}}":"{{int:abusefilter-disabled}}")).'
|'.(isset($AF["private"])?"{{int:abusefilter-hidden}}":"{{int:abusefilter-unhidden}}").'
|data-sort-value='.$AF["hits"].'| [{{fullurl:Special:AbuseLog|wpSearchFilter='.$AF["id"].'}} '.$AFhitstext.']
';
	$outcsv []= [
		$AF["id"],
		$AF["description"],
		$AF["actions"],
		(isset($AF["enabled"])?"enabled":(isset($AF["deleted"])?"deleted":"disabled")),
		(isset($AF["private"])?"hidden":"unhidden"),
		$AF["hits"]
	];
}
$out .= '|}';

$fp = fopen(__DIR__."/abusefilter_list.csv", "w");
foreach ($outcsv as $row) {
    fputcsv($fp, $row);
}
fclose($fp);

$starttimestamp = time();
$res = cURL($C["wikiapi"]."?".http_build_query(array(
	"action" => "query",
	"prop" => "revisions",
	"format" => "json",
	"rvprop" => "content|timestamp",
	"titles" => $C["outpage"]
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
$pages = current($res["query"]["pages"]);
$text = $pages["revisions"][0]["*"];
$basetimestamp = $pages["revisions"][0]["timestamp"];

$start = strpos($text, $C["text1"]);
$end = strpos($text, $C["text2"]);
$text = substr($text, 0, $start).$C["text1"].$out.substr($text, $end);

$start = strpos($text, $C["text3"]);
$end = strpos($text, $C["text4"]);
$text = substr($text, 0, $start).$C["text3"]."~~~~~".substr($text, $end);

$summary = $C["summary_prefix"]."更新";
$post = array(
	"action" => "edit",
	"format" => "json",
	"title" => $C["outpage"],
	"summary" => $summary,
	"text" => $text,
	"minor" => "",
	"token" => $edittoken
);
echo "edit ".$C["outpage"]." summary=".$summary."\n";
if (!$C["test"]) {
	$res = cURL($C["wikiapi"], $post);
} else {
	$res = false;
	file_put_contents(__DIR__."/out.txt", $text);
}
$res = json_decode($res, true);
if (isset($res["error"])) {
	echo "edit fail\n";
}
