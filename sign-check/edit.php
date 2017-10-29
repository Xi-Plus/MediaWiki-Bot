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
require(__DIR__."/function.php");

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login("bot");
$edittoken = edittoken();

$timelimit = date("Y-m-d H:i:s", strtotime($C["timelimit"]));
echo "report lastedit > ".$timelimit." (".$C["timelimit"].")\n";
echo "fetch from database\n";
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist` WHERE `lastedit` > :lastedit ORDER BY `signlen` DESC");
$sth->bindValue(":lastedit", $timelimit);
$sth->execute();
$userlist = $sth->fetchAll(PDO::FETCH_ASSOC);

echo "start table\n";
for ($i=0; $i < $C["fail_retry"]; $i++) {
	$out = '{| class="wikitable sortable"
!使用者
!簽名
!字數
!位元組
';
	foreach ($userlist as $user) {
		$userpage = "[[User talk:".$user["name"]."|".$user["name"]."]]";
		$sign = $user["sign"];
		$len = mb_strlen($sign);
		$byte = strlen($sign);
		if ($byte >= 300) {
			$byte = "{{red|'''".$byte."'''}}";
		}
		$out .= '|-
|'.$userpage.'
| '.$sign.'
|'.$len.'
|'.$byte.'
';
	}
	$out .= '|}';

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
	$end = strpos($text, $C["text2"]);
	$text = substr($text, 0, $start).$C["text1"].$out.substr($text, $end);

	$start = strpos($text, $C["text3"]);
	$end = strpos($text, $C["text4"]);
	$text = substr($text, 0, $start).$C["text3"]."~~~~".substr($text, $end);

	$summary = $C["summary_prefix"]."更新";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $C["page"],
		"summary" => $summary,
		"text" => $text,
		"minor" => "",
		"token" => $edittoken
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
		continue;
	}
	break;
}
