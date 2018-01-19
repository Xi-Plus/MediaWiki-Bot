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

if (isset($argv[1])) {
	$page = trim($argv[1]);
} else {
	echo "input page:";
	$page = trim(fgets(STDIN));
}
$pageregex = $page;
$pageregex = preg_replace("/\(/", "\(", $pageregex);
$pageregex = preg_replace("/\)/", "\)", $pageregex);
$pageregex = preg_replace("/( |_)/", "(?: |_)", $pageregex);
echo "fix \"".$page."\" (".$pageregex.")\n";

$res = cURL($C["wikiapi"]."?".http_build_query(array(
	"action" => "query",
	"prop" => "revisions",
	"format" => "json",
	"rvprop" => "content|timestamp",
	"titles" => $page
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
$pages = current($res["query"]["pages"]);
$text = $pages["revisions"][0]["*"];
if (preg_match("/#(?:重定向|Redirect) *\[\[(.+?)]]/i", $text, $m)) {
	$target = $m[1];
	echo "Redirect to \"".$target."\"\n";
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"format" => "json",
		"list" => "backlinks",
		"bltitle" => $page,
		"bllimit" => "max",
		"blnamespace" => $C["fix_ns"]
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	foreach ($res["query"]["backlinks"] as $backlink) {
		$title = $backlink["title"];
		echo "backlink:\"".$title."\"\n\n";

		$starttimestamp = time();
		$res2 = cURL($C["wikiapi"]."?".http_build_query(array(
			"action" => "query",
			"prop" => "revisions",
			"format" => "json",
			"rvprop" => "content|timestamp",
			"titles" => $title
		)));
		if ($res2 === false) {
			exit("fetch page fail\n");
		}
		$res2 = json_decode($res2, true);
		$pages = current($res2["query"]["pages"]);
		$oldtext = $pages["revisions"][0]["*"];
		$basetimestamp = $pages["revisions"][0]["timestamp"];

		$newtext = $oldtext;
		if (preg_match_all("/\[\[(".$pageregex.")(?:\|.+?)?]]/", $newtext, $m)) {
			foreach ($m[0] as $key => $value) {
				echo "find:\"\033[32m".$m[0][$key]."\033[37m\"\n\n";
				echo "context:".substr($newtext, strpos($newtext, $m[0][$key])-$C["context_before"], $C["context_before"]+strlen($m[0][$key])+$C["context_after"])."\n\n";
				$replace = str_replace($m[1][$key], $target, $m[0][$key]);
				$replace = str_replace("[[".$target."|".$target."]]", "[[".$target."]]", $replace);
				echo "replace to \"\033[32m".$replace."\033[37m\"\n";
				echo "check (y/n)?";
				$check = trim(fgets(STDIN));
				if (strlen($check) > 0 && $check[0] == "y") {
					$newtext = str_replace($m[0][$key], $replace, $newtext);
				}
			}
		} else {
			echo "no match [[1]]\n";
		}
		if (preg_match_all("/{{link-..\|(?:".$pageregex.")\|[^|]+}}/", $newtext, $m)) {
			foreach ($m[0] as $key => $value) {
				echo "find:\"\033[32m".$m[0][$key]."\033[37m\"\n\n";
				echo "context:".substr($newtext, strpos($newtext, $m[0][$key])-$C["context_before"], $C["context_before"]+strlen($m[0][$key])+$C["context_after"])."\n\n";
				$replace = str_replace($m[0][$key], "[[".$target."]]", $m[0][$key]);
				echo "replace to \"\033[32m".$replace."\033[37m\"\n";
				echo "check (y/n)?";
				$check = trim(fgets(STDIN));
				if (strlen($check) > 0 && $check[0] == "y") {
					$newtext = str_replace($m[0][$key], $replace, $newtext);
				}
			}
		} else {
			echo "no match {{link-xx|1|2}}\n";
		}
		if (preg_match_all("/{{link-..\|(?:".$pageregex.")\|[^|]+\|([^}]+)}}/", $newtext, $m)) {
			foreach ($m[0] as $key => $value) {
				echo "find:\"\033[32m".$m[0][$key]."\033[37m\"\n\n";
				echo "context:".substr($newtext, strpos($newtext, $m[0][$key])-$C["context_before"], $C["context_before"]+strlen($m[0][$key])+$C["context_after"])."\n";
				if ($target == $m[1][$key]) {
					$replace = str_replace($m[0][$key], "[[".$target."]]", $m[0][$key]);
				} else {
					$replace = str_replace($m[0][$key], "[[".$target."|".$m[1][$key]."]]", $m[0][$key]);
				}
				echo "replace to \"\033[32m".$replace."\033[37m\"\n";
				echo "check (y/n)?";
				$check = trim(fgets(STDIN));
				if (strlen($check) > 0 && $check[0] == "y") {
					$newtext = str_replace($m[0][$key], $replace, $newtext);
				}
			}
		} else {
			echo "no match {{link-xx|1|2|3}}\n";
		}

		if ($oldtext != $newtext) {
			$summary = $C["summary_prefix"];
			$post = array(
				"action" => "edit",
				"format" => "json",
				"title" => $title,
				"summary" => $summary,
				"text" => $newtext,
				"token" => $edittoken,
				"minor" => "",
				"starttimestamp" => $starttimestamp,
				"basetimestamp" => $basetimestamp
			);
			echo "edit ".$title." summary=".$summary."\n\n";
			if (!$C["test"]) $res = cURL($C["wikiapi"], $post);
			else {
				file_put_contents("out.txt", $newtext);
				$res = false;
			}
			$res = json_decode($res, true);
			if (isset($res["error"])) {
				echo "edit fail\n";
				if ($i === 1) {
					exit("quit\n");
				} else {
					echo "retry\n";
				}
			} else {
			}
		} else {
			echo "no chagnes\n";
		}
	}
} else {
	echo "error: no match redirect\n";
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
