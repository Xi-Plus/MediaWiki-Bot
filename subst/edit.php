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

$nexttime = file_get_contents(__DIR__."/nexttime.txt");
if ($nexttime === false) {
	exit("read nexttime fail\n");
}
if (time() < $nexttime) {
	exit("next edit is ".date("Y-m-d H:i:s", $nexttime).", not yet\n");
}

login();
$edittoken = edittoken();

$month = date("n");
$date = date("j");
$tag_timestamp = mktime(0, 0, 0, $month, $date)+86400*7;
echo "tag ".$month."月".$date."日 (timestamp > ".$tag_timestamp.")\n";

$pagelist = file_get_contents(__DIR__."/input.txt");
if ($pagelist === false) {
	exit("read input fail\n");
}
$pagelist = str_replace("\r\n", "\n", $pagelist);
$pagelist = explode("\n", $pagelist);

$count = rand(2, 3);
echo "edit ".$count." pages\n";

for ($j=0; $j < $count; $j++) { 
	for ($i=$C["fail_retry"]; $i > 0; $i--) {
		$page = $pagelist[$j];
		echo "edit ".$page."\n";

		$starttimestamp = time();
		$res = cURL($C["wikiapi"]."?".http_build_query(array(
			"action" => "query",
			"prop" => "revisions",
			"format" => "json",
			"rvprop" => "content|timestamp",
			"titles" => $page
		)));
		if ($res === false) {
			echo "fetch page fail\n";
			continue;
		}
		$res = json_decode($res, true);
		$pages = current($res["query"]["pages"]);
		$text = $pages["revisions"][0]["*"];
		$basetimestamp = $pages["revisions"][0]["timestamp"];
		echo "get main page\n";
		file_put_contents("../tmp/1.txt", $text);
		$text = preg_replace("/{{(CopyvioNotice|侵权留言提示)\|(.+?)}}/i", "{{subst:User:A2093064/cvnnosign|$1}}", $text);
		$text = preg_replace("/{{(CopyvioNotice|侵权留言提示)}}/i", "{{subst:CopyvioNotice/old}}", $text);
		file_put_contents("../tmp/2.txt", $text);

		echo "start edit\n";

		echo "edit main page\n";
		$summary = $C["summary_prefix"]."處理未subst的{{CopyvioNotice}}";
		$post = array(
			"action" => "edit",
			"format" => "json",
			"title" => $page,
			"summary" => $summary,
			"text" => $text,
			"token" => $edittoken,
			"minor" => "",
			"starttimestamp" => $starttimestamp,
			"basetimestamp" => $basetimestamp
		);
		echo "edit ".$page." summary=".$summary."\n";
		if (!$C["test"]) $res = cURL($C["wikiapi"], $post);
		else $res = false;
		$res = json_decode($res, true);
		if (isset($res["error"])) {
			echo "edit fail\n";
			if ($i === 1) {
				echo "quit\n";
			} else {
				echo "retry\n";
			}
		} else {
			unset($pagelist[$j]);
			break;
		}
	}
}

file_put_contents(__DIR__."/input.txt", implode("\n", $pagelist));

$nexttime = time()+60*rand(8, 15);
file_put_contents(__DIR__."/nexttime.txt", $nexttime);
echo "next edit: ".date("Y-m-d H:i:s", $nexttime)."\n";

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
