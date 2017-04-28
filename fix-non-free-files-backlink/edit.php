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
require(__DIR__."/../function/log.php");

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login();
$edittoken = edittoken();

$count = 0;
foreach ($C["category"] as $category) {
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"format" => "json",
		"list" => "categorymembers",
		"cmtitle" => $category,
		"cmnamespace" => "6",
		"cmlimit" => "max"
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pagelist = $res["query"]["categorymembers"];
	foreach ($pagelist as $page) {
		echo $page["title"]."\n";
		$res = cURL($C["wikiapi"]."?".http_build_query(array(
			"action" => "query",
			"format" => "json",
			"prop" => "fileusage",
			"pageids" => $page["pageid"]
		)));
		if ($res === false) {
			exit("fetch page fail\n");
		}
		$res = json_decode($res, true);
		$pages = current($res["query"]["pages"]);
		if (!isset($pages["fileusage"])) {
			echo "no use\n";
			WriteLog($page["title"]." no use");
			continue;
		}
		if (count($pages["fileusage"]) > 1) {
			echo "use more than 1\n";
			WriteLog($page["title"]." be used ".count($pages["fileusage"])." times");
			continue;
		}
		$article = $pages["fileusage"][0]["title"];
		WriteLog("fix ".$page["title"]." to ".$article);
		echo $article."\n";
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

			if (preg_match_all("/\| *Article *= *.+$/mi", $text, $m) !== 1) {
				echo "not match 1 time\n";
				WriteLog($page["title"]." not match 1 time");
				break;
			}

			$text = preg_replace("/(\| *Article *=).+$/mi", '${1} '.$article, $text);

			$summary = $C["summary_prefix"]."，修正[[:".$category."]]";
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
				$count ++;
				if ($count >= $C["max_edits_one_time"]) {
					break 3;
				}
				break;
			}
		}
	}
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
