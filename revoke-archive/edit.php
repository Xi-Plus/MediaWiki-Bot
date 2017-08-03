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

function converttime($chitime){
	if (preg_match("/(\d{4})年(\d{1,2})月(\d{1,2})日 \(.{3}\) (\d{2})\:(\d{2}) \(UTC\)/", $chitime, $m)) {
		return strtotime($m[1]."/".$m[2]."/".$m[3]." ".$m[4].":".$m[5]);
	} else {
		exit("converttime fail\n");
	}
}
function TimediffFormat($time) {
	if ($time<60) return $time."秒";
	if ($time<60*50) return round($time/60)."分";
	if ($time<60*60*23.5) return round($time/(60*60))."小時";
	return round($time/(60*60*24))."天";
}

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login();
$edittoken = edittoken();

$retention_time = array();
for ($i=1; $i <= 4; $i++) { 
	$retention_time[$i] = @file_get_contents($C["retention_time_{$i}"]);
	if ($retention_time[$i] === false) {
		$retention_time[$i] = $C["retention_time_{$i}_default"];
		echo "Warning: fetch retention_time_{$i} fail, use default value\n";
	}
	echo "{$i}. archive before ".$retention_time[$i]." ago (".date("Y-m-d H:i:s", time()-$retention_time[$i]).")\n";
}

$revoketime = strtotime("-6 months");

for ($i=$C["fail_retry"]; $i > 0; $i--) {
	$starttimestamp = time();
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $C["from_page"]
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	$text = $pages["revisions"][0]["*"];
	$basetimestamp = $pages["revisions"][0]["timestamp"];
	echo "get main page\n";

	$hash = md5(uniqid(rand(), true));

	$text = preg_replace("/^( *== *{$C['text1']} *== *)$/m", $hash."$1", $text);
	$text = preg_replace("/^( *== *{$C['text2']} *== *)$/m", $hash."$1", $text);
	$text = preg_replace("/^( *== *{$C['text3']} *== *)$/m", $hash."$1", $text);
	$text = preg_replace("/^( *== *{$C['text4']} *== *)$/m", $hash."$1", $text);
	$text = preg_replace("/^( *{$C['text5']} *)$/m", $hash."$1", $text);

	$text = explode($hash, $text);
	if (count($text) != 6) {
		exit("split error\n");
	}
	echo "split ok\n";
	$oldpagetext = $text[0];
	$newpagetext = array();
	$archive_count = array("all" => 0);

	for ($i=1; $i <= 4; $i++) { 
		$text[$i] = preg_replace("/^(\*{{User\|.+}} *)$/m", $hash."$1", $text[$i]);
		$text[$i] = explode($hash, $text[$i]);
		echo "section {$i} find ".(count($text[$i])-1)." revoke\n";
		$oldpagetext .= $text[$i][0];
		if (count($text[$i]) > 1) {
			unset($text[$i][0]);
			foreach ($text[$i] as $temp) {
				preg_match("/{{User\|(.+)}}/", $temp, $m);
				echo $m[1]."\t";
				preg_match("/{{status2\|(.+?)(\||}})/", $temp, $m);
				echo "status ".$m[1]."\t";
				if ($m[1] == "+" || $m[1] == "-") {
					preg_match_all("/\d{4}年\d{1,2}月\d{1,2}日 \(.{3}\) \d{2}\:\d{2} \(UTC\)/", $temp, $m);
					$firsttime = time();
					$lasttime = 0;
					foreach ($m[0] as $timestr) {
						$time = converttime($timestr);
						if ($time < $revoketime) continue;
						if ($time > $lasttime) $lasttime = $time;
						if ($time < $firsttime) $firsttime = $time;
					}
					echo "firsttime=".date("Y/m/d H:i:s", $firsttime)."\t";
					echo "lasttime=".date("Y/m/d H:i:s", $lasttime)."\t";
					if (time()-$lasttime > $retention_time[$i]) {
						echo "archive\t";
						$year = date("Y", $firsttime);
						if (!isset($newpagetext[$year])) {
							$newpagetext[$year] = array();
							$archive_count[$year] = 0;
						}
						if (!isset($newpagetext[$year][$i])) {
							$newpagetext[$year][$i] = array();
						}
						$newpagetext[$year][$i] []= $temp;
						$archive_count[$year]++;
						$archive_count["all"]++;
					} else {
						echo "not archive\t";
						$oldpagetext .= $temp;
					}
				} else {
					echo "pass";
					$oldpagetext .= $temp;
				}
				echo "\n";
			}
		}
	}
	$oldpagetext .= $text[5];

	if ($archive_count["all"] === 0) {
		exit("no change\n");
	}

	echo "start edit\n";

	echo "edit main page\n";
	$summary = $C["summary_prefix"]."：存檔".$archive_count["all"]."請求至".count($newpagetext)."頁面 (".$C["summary_config_page"]."：".TimediffFormat($retention_time[1]).",".TimediffFormat($retention_time[2]).",".TimediffFormat($retention_time[3]).",".TimediffFormat($retention_time[4]).")";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $C["from_page"],
		"summary" => $summary,
		"text" => $oldpagetext,
		"token" => $edittoken,
		"minor" => "",
		"starttimestamp" => $starttimestamp,
		"basetimestamp" => $basetimestamp
	);
	echo "edit ".$C["from_page"]." summary=".$summary."\n";
	if (!$C["test"]) $res = cURL($C["wikiapi"], $post);
	else {
		$res = false;
		file_put_contents(str_replace("/", "-", $C["from_page"]).".txt", $oldpagetext);
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
		break;
	}
}

echo "edit archive page\n";
foreach ($newpagetext as $year => $newtext) {
	$page = $C["to_page_prefix"].$year."年";
	for ($i=$C["fail_retry"]; $i > 0; $i--) { 
		$starttimestamp2 = time();
		$res = cURL($C["wikiapi"]."?".http_build_query(array(
			"action" => "query",
			"prop" => "revisions",
			"format" => "json",
			"rvprop" => "content|timestamp",
			"titles" => $page
		)));
		$res = json_decode($res, true);
		$pages = current($res["query"]["pages"]);

		$text = "{{存档页|Wikipedia:申请解除权限}}\n".
			"=={$C['text1']}==\n".
			"=={$C['text2']}==\n".
			"=={$C['text3']}==\n".
			"=={$C['text4']}\n";

		$basetimestamp2 = null;
		if (!isset($pages["missing"])) {
			$text = $pages["revisions"][0]["*"];
			$basetimestamp2 = $pages["revisions"][0]["timestamp"];
			echo $page." exist\n";
		} else {
			echo $page." not exist\n";
		}

		$hash = md5(uniqid(rand(), true));
		$text = preg_replace("/^( *== *{$C['text1']} *== *)$/m", $hash."$1", $text);
		$text = preg_replace("/^( *== *{$C['text2']} *== *)$/m", $hash."$1", $text);
		$text = preg_replace("/^( *== *{$C['text3']} *== *)$/m", $hash."$1", $text);
		$text = preg_replace("/^( *== *{$C['text4']} *== *)$/m", $hash."$1", $text);

		$text = explode($hash, $text);
		if (count($text) != 5) {
			exit("split error\n");
		}
		echo "split ok\n";

		foreach ($newtext as $section => $newtext2) {
			$text[$section] .= "\n".implode("\n", $newtext2);
		}

		$text = implode("\n", $text);
		$text = preg_replace("/\n{3,}/", "\n\n", $text);

		$summary = $C["summary_prefix"]."：存檔自[[".$C["from_page"]."]]共".$archive_count[$year]."個請求";
		$post = array(
			"action" => "edit",
			"format" => "json",
			"title" => $page,
			"summary" => $summary,
			"text" => $text,
			"token" => $edittoken,
			"minor" => "",
			"starttimestamp" => $starttimestamp2
		);
		if ($basetimestamp2 !== null) {
			$post["basetimestamp"] = $basetimestamp2;
		}
		echo "edit ".$page." summary=".$summary."\n";
		if (!$C["test"]) $res = cURL($C["wikiapi"], $post);
		else {
			$res = false;
			file_put_contents(str_replace("/", "-", $page).".txt", $text);
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
			break;
		}
	}
	echo "saved\n";
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
