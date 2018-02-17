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

$options = getopt("", ["target:", "summary:", "page:", "copy:"]);
if ($options === false) {
	exit("parse parameter failed\n");
}
if (isset($options["target"])) {
	$target = $options["target"];
	if (!isset($C["target"][$target])) {
		exit("target not accepted: ".implode("、", array_keys($C["target"]))."\n");
	}
	foreach ($C["target"][$target] as $key => $value) {
		$C[$key] = $value;
	}
} else {
	exit("target requireed: ".implode("、", array_keys($C["target"]))."\n");
}
if (isset($options["page"])) {
	$page = $options["page"];
	$page = preg_replace("/^Mediawiki:/i", "", $page);
	$page = preg_replace("/^([^\/]+).*$/", "$1", $page);
} else {
	exit("page requireed\n");
}
$copylist = [];
if (isset($options["copy"])) {
	if (is_array($options["copy"])) {
		foreach ($options["copy"] as $copy) {
			if (!isset($C["target"][$target]["copylist"][$copy])) {
				exit("--copy ".$copy." not found\n");
			} else {
				$copylist[]= $copy;
			}
		}
	} else {
		if (!isset($C["target"][$target]["copylist"][$options["copy"]])) {
			exit("--copy ".$options["copy"]." not found\n");
		} else {
			$copylist[]= $options["copy"];
		}
	}
} else {
	exit("nothing to do\n");
}
if (isset($options["summary"])) {
	$C["summary_prefix"] = $options["summary"];
}
echo "target = ".$C["wikiapi"]."\n";
echo "page = ".$page."\n";

login($C["bot"]?"bot":"user");
$edittoken = edittoken();

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

$exist = [];
$summarylist = [];
foreach ($copylist as $copy) {
	echo "copylist: ".$copy."\n\n";
	foreach ($C["target"][$target]["copylist"][$copy] as $temp) {
		$from = $temp[0];
		$to = $temp[1];
		echo "copy ".$from." to ".$to."\n";
		if (!isset($exist[$from])) {
			$res = cURL($C["wikiapi"]."?".http_build_query(array(
				"action" => "query",
				"prop" => "revisions",
				"format" => "json",
				"rvprop" => "timestamp|comment",
				"titles" => "Mediawiki:".$page.$from
			)));
			$res = json_decode($res, true);
			$pages = current($res["query"]["pages"]);
			if (isset($pages["missing"])) {
				$exist[$from] = false;
			} else {
				$exist[$from] = true;
				$summarylist[$from] = $pages["revisions"][0]["comment"];
			}
		}
		if ($exist[$from] === true) {
			$summary = $summarylist[$from];
			$topage = "Mediawiki:".$page.$to;
			$text = "{{subst:msgnw:MediaWiki:".$page.$from."}}";
			$post = array(
				"action" => "edit",
				"format" => "json",
				"title" => $topage,
				"summary" => $summary,
				"text" => $text,
				"token" => $edittoken
			);
			if (isset($C["bot"])) {
				$post["bot"] = "";
			}
			echo "edit ".$topage."\n";
			echo "summary = ".$summary."\n";
			echo "text = ".$text."\n";
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
		} else {
			echo "Mediawiki:".$page.$from." not exist\n";
		}
		echo "\n";
	}
}
