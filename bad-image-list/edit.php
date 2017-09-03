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

for ($i=0; $i < $C["fail_retry"]; $i++) { 
	$text = file_get_contents($C["page"]);
	if ($text === false) {
		echo "fetch fail\n";
		continue;
	}
	$entext = file_get_contents($C["page2"]);
	if ($entext === false) {
		echo "fetch fail\n";
		continue;
	}

	$hash = md5(uniqid(rand(), true));
	echo "hash ".$hash."\n";
	$text = preg_replace("/^(\* \[\[:File:.+?)\n([^*])/m", "$1".$hash."$2", $text);
	$text = explode($hash, $text);
	echo "find ".count($text)." sections\n";
	if (count($text) != 3) {
		echo "split fail\n";
		continue;
	}

	$exist = [];
	$out = "";
	foreach ($text as $temp) {
		if (strpos($temp, $C["text1"]) !== false) {
			$out .= "\n";
			$temp = explode("\n", $temp);
			$except = [];
			foreach ($temp as $temp2) {
				if (preg_match("/^\* \[\[(:File:[^]]+)\]\](.*)$/i", $temp2, $m)) {
					$file = $m[1];
					$file = str_replace("_", " ", $file);
					$except[$file] = [];
					if (preg_match_all("/\[\[([^]]+?)\]\]/", $m[2], $m2)) {
						foreach ($m2[1] as $page) {
							$page = str_replace("_", " ", $page);
							$except[$file] []= $page;
						}
					}
				} else {
					$out .= "\n".$temp2."\n";
				}
			}
			preg_match_all("/^\* \[\[(:File:[^]]+)/mi", $entext, $m);
			foreach ($m[1] as $file) {
				$file = str_replace("_", " ", $file);
				$out .= "* [[".$file."]]";
				if (isset($except[$file]) && count($except[$file]) > 0) {
					$out .= " except on [[".implode("]], [[", $except[$file])."]]";
				}
				$out .= "\n";
				unset($except[$file]);
			}
			$out .= "\n";
		} else {
			$out .= "\n".$temp."\n";
		}
	}
	$out = preg_replace("/^\n+/", "", $out);
	$out = preg_replace("/\n+$/", "", $out);
	$out = preg_replace("/\n{3,}/", "\n\n", $out);
	$date = date("Y/m/d");
	$out = preg_replace("/更新至\d+\/\d+\/\d+/", "更新至".$date, $out);

	$summary = $C["summary_prefix"]."更新";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $C["outpage"],
		"summary" => $summary,
		"text" => $out,
		"minor" => "",
		"token" => $edittoken
	);
	echo "edit ".$C["outpage"]." summary=".$summary."\n";
	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
		file_put_contents("out.txt", $out);
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		continue;
	}

	$remove = "";
	foreach ($except as $page => $temp) {
		$remove .= "* [[".$page."]]\n";
	}
	file_put_contents("remove.txt", $remove);

	break;
}
